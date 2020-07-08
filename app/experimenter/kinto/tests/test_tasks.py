import datetime

import mock
from django.conf import settings
from django.test import TestCase

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.kinto.tests.mixins import MockKintoClientMixin
from experimenter.kinto import tasks
from experimenter.experiments.api.v1.serializers import ExperimentRapidRecipeSerializer


class TestPushExperimentToKintoTask(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, proposed_start_date=datetime.date(2020, 1, 20)
        )

    def test_push_experiment_to_kinto_sends_experiment_data(self):
        tasks.push_experiment_to_kinto(self.experiment.id)

        data = ExperimentRapidRecipeSerializer(self.experiment).data

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
            type=Experiment.TYPE_RAPID,
            bugzilla_id="12345",
            name="test",
            firefox_min_version=Experiment.VERSION_CHOICES[0][0],
            firefox_max_version=None,
            firefox_channel=Experiment.CHANNEL_RELEASE,
        )
        self.setup_kinto_no_pending_review()
        tasks.check_kinto_push_queue()
        self.mock_push_task.assert_called_with(experiment.id)
