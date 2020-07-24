import datetime

import mock
from django.conf import settings
from django.test import TestCase

from mozilla_nimbus_shared import get_data

from experimenter.experiments.models import Experiment, ExperimentBucketRange
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.kinto.tests.mixins import MockKintoClientMixin
from experimenter.kinto import tasks
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer

NIMBUS_DATA = get_data()


class TestPushExperimentToKintoTask(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            proposed_start_date=datetime.date(2020, 1, 20),
            normandy_slug="normandy-slug",
            audience="us_only",
        )

    def test_push_experiment_to_kinto_sends_experiment_data(self):
        tasks.push_experiment_to_kinto(self.experiment.id)

        data = ExperimentRapidRecipeSerializer(self.experiment).data

        self.assertTrue(
            ExperimentBucketRange.objects.filter(experiment=self.experiment).exists()
        )

        bucketConfig = data["arguments"]["bucketConfig"]["count"]

        designPreset = NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"][
            "arguments"
        ]["bucketConfig"]["count"]

        self.assertEqual(bucketConfig, designPreset)

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION,
            bucket=settings.KINTO_BUCKET,
            if_not_exists=True,
        )

    def test_push_experiment_to_kinto_reraises_exception(self):
        self.mock_kinto_client.create_record.side_effect = Exception

        with self.assertRaises(Exception):
            tasks.push_experiment_to_kinto(self.experiment.id)


class TestCheckKintoPushQueue(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        mock_push_task_patcher = mock.patch(
            "experimenter.kinto.tasks.push_experiment_to_kinto.delay"
        )
        self.mock_push_task = mock_push_task_patcher.start()
        self.addCleanup(mock_push_task_patcher.stop)

    def test_check_with_empty_queue_pushes_nothing(self):
        tasks.check_kinto_push_queue()
        self.mock_push_task.assert_not_called()

    def test_check_with_no_review_status_pushes_nothing(self):
        for status in [
            Experiment.STATUS_DRAFT,
            Experiment.STATUS_ACCEPTED,
            Experiment.STATUS_LIVE,
            Experiment.STATUS_COMPLETE,
        ]:
            ExperimentFactory.create(type=Experiment.TYPE_RAPID, status=status)

        tasks.check_kinto_push_queue()
        self.mock_push_task.assert_not_called()

    def test_check_with_review_non_rapid_pushes_nothing(self):
        ExperimentFactory.create(
            type=Experiment.TYPE_ADDON, status=Experiment.STATUS_REVIEW
        )
        tasks.check_kinto_push_queue()
        self.mock_push_task.assert_not_called()

    def test_check_with_rapid_review_and_kinto_pending_pushes_nothing(self):
        ExperimentFactory.create(
            type=Experiment.TYPE_RAPID, status=Experiment.STATUS_REVIEW,
        )
        self.setup_kinto_pending_review()
        tasks.check_kinto_push_queue()
        self.mock_push_task.assert_not_called()

    def test_check_with_rapid_review_and_no_kinto_pending_pushes_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            bugzilla_id="12345",
            firefox_channel=Experiment.CHANNEL_RELEASE,
            firefox_max_version=None,
            firefox_min_version=Experiment.VERSION_CHOICES[0][0],
            name="test",
            type=Experiment.TYPE_RAPID,
        )
        self.assertEqual(experiment.changes.count(), 2)

        self.setup_kinto_no_pending_review()
        tasks.check_kinto_push_queue()
        self.mock_push_task.assert_called_with(experiment.id)

        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.changes.count(), 3)
        self.assertEqual(experiment.status, Experiment.STATUS_ACCEPTED)
        self.assertEqual(experiment.proposed_start_date, datetime.date.today())
        self.assertEqual(experiment.firefox_min_version, Experiment.VERSION_CHOICES[0][0])
        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)
        self.assertEqual(experiment.normandy_slug, "bug-12345-rapid-test-release-55")
