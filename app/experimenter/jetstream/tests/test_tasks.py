import datetime
import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.jetstream import tasks
from experimenter.jetstream.tests.constants import TestConstants
from experimenter.jetstream.tests.factory import JetstreamDataFactory


@override_settings(FEATURE_ANALYSIS=False)
class TestFetchJetstreamDataTask(TestCase):
    maxDiff = None

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_not_null(self, lifecycle, mock_exists, mock_open):
        (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
        ) = TestConstants.get_test_data()

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    return "{}"
                return json.dumps(DAILY_DATA)

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True
        primary_outcome = "primary_outcome"
        secondary_outcome = "secondary_outcome"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=[primary_outcome],
            secondary_outcomes=[secondary_outcome],
        )

        results_data = JetstreamDataFactory().generate_results_data(
            experiment.primary_outcomes
        )

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.results_data, results_data)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_null(self, lifecycle, mock_exists):
        mock_exists.return_value = False
        primary_outcome = "outcome"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, primary_outcomes=[primary_outcome]
        )

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            experiment.results_data,
            {
                "daily": None,
                "metadata": None,
                "overall": None,
                "show_analysis": False,
                "weekly": None,
            },
        )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_in_loop(self, lifecycle, mock_delay):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_expired_in_loop(self, lifecycle, mock_delay):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        experiment.results_data = {
            "daily": None,
            "metadata": None,
            "overall": None,
            "show_analysis": False,
            "weekly": None,
        }
        experiment.save()
        experiment.changes.all().filter(
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        ).update(changed_on=datetime.date.today() - datetime.timedelta(days=4))
        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_null_fetches(self, lifecycle, mock_delay):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        experiment.changes.all().filter(
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        ).update(changed_on=datetime.date.today() - datetime.timedelta(days=4))
        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_no_data_fetch_in_loop(self, lifecycle, mock_delay):
        NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_exception_for_fetch_jetstream_data(self, mock_delay):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )
        mock_delay.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.fetch_jetstream_data()

    @patch("experimenter.jetstream.tasks.get_experiment_data")
    def test_exception_for_fetch_experiment_data(self, mock_get_experiment_data):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )
        mock_get_experiment_data.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.fetch_experiment_data(experiment.id)
