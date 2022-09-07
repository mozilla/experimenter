import datetime
import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.jetstream import tasks
from experimenter.jetstream.models import Group
from experimenter.jetstream.tests import mock_valid_outcomes
from experimenter.jetstream.tests.constants import (
    JetstreamTestData,
    NonePointJetstreamTestData,
    ZeroJetstreamTestData,
)
from experimenter.outcomes import Outcomes


@mock_valid_outcomes
@override_settings(FEATURE_ANALYSIS=False)
class TestFetchJetstreamDataTask(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        Outcomes.clear_cache()

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_valid_results_data_parsed_and_stored(
        self, lifecycle, mock_exists, mock_open
    ):
        primary_outcomes = ["default-browser"]
        secondary_outcomes = ["secondary_outcome"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
            secondary_outcomes=secondary_outcomes,
        )
        experiment.reference_branch.slug = "control"
        experiment.reference_branch.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.slug = "variant"
        treatment_branch.save()

        (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
        ) = JetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "daily": DAILY_DATA,
            "weekly": WEEKLY_DATA,
            "overall": OVERALL_DATA,
            "other_metrics": {
                Group.OTHER: {
                    "some_count": "Some Count",
                    "another_count": "Another Count",
                },
            },
            "metadata": {
                "outcomes": {
                    "default-browser": {
                        "metrics": [
                            "default_browser_action",
                            "mozilla_default_browser",
                            "default_browser_null",
                        ],
                        "default_metrics": [],
                    }
                }
            },
            "show_analysis": False,
        }

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    return """{
                        "outcomes": {
                            "default-browser": {
                                "metrics": [
                                    "default_browser_action",
                                    "mozilla_default_browser",
                                    "default_browser_null"
                                ],
                                "default_metrics": []
                            }
                        }
                    }"""
                return json.dumps(DAILY_DATA)

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.results_data, FULL_DATA)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_with_zeros_parsed_and_stored(
        self, lifecycle, mock_exists, mock_open
    ):
        primary_outcomes = ["default-browser"]
        secondary_outcomes = ["secondary_outcome"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
            secondary_outcomes=secondary_outcomes,
        )
        experiment.reference_branch.slug = "control"
        experiment.reference_branch.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.slug = "variant"
        treatment_branch.save()

        (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
        ) = ZeroJetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "daily": DAILY_DATA,
            "weekly": WEEKLY_DATA,
            "overall": OVERALL_DATA,
            "other_metrics": {
                Group.OTHER: {
                    "some_count": "Some Count",
                    "another_count": "Another Count",
                },
            },
            "metadata": {},
            "show_analysis": False,
        }

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

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.results_data, FULL_DATA)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.client.get_metadata")
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_with_null_conversion_percent(
        self, lifecycle, mock_exists, mock_open, mock_get_metadata
    ):
        primary_outcomes = ["default-browser"]
        secondary_outcomes = ["secondary_outcome"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
            secondary_outcomes=secondary_outcomes,
        )
        experiment.reference_branch.slug = "control"
        experiment.reference_branch.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.slug = "variant"
        treatment_branch.save()

        (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
        ) = NonePointJetstreamTestData.get_test_data(primary_outcomes)

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

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertIsNone(experiment.results_data)

        mock_get_metadata.return_value = {
            "outcomes": {"default-browser": {"metrics": ["test"], "default_metrics": []}}
        }

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertIsNotNone(experiment.results_data)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_null(self, lifecycle, mock_exists):
        mock_exists.return_value = False
        primary_outcome = "default-browser"
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=4)
        )
        experiment.results_data = {
            "daily": None,
            "metadata": None,
            "overall": None,
            "show_analysis": False,
            "weekly": None,
        }
        experiment.save()

        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_null_fetches(self, lifecycle, mock_delay):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=4)
        )

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
