import datetime
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
