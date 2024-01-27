import datetime
import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from mozilla_nimbus_schemas.jetstream import SampleSizesFactory
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.jetstream import tasks
from experimenter.jetstream.client import get_data
from experimenter.jetstream.models import AnalysisWindow, Group
from experimenter.jetstream.tests import mock_valid_outcomes
from experimenter.jetstream.tests.constants import (
    JetstreamTestData,
    NonePointJetstreamTestData,
    ZeroJetstreamTestData,
)
from experimenter.jetstream.tests.mixins import MockSizingDataMixin
from experimenter.outcomes import Outcomes
from experimenter.settings import SIZING_DATA_KEY


@mock_valid_outcomes
@override_settings(FEATURE_ANALYSIS=False)
class TestFetchJetstreamDataTask(MockSizingDataMixin, TestCase):
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
            ERRORS,
            SEGMENT_DATA,
            DAILY_EXPOSURES_DATA,
            SEGMENT_EXPOSURES_DATA,
        ) = JetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "v2": {
                "daily": {"enrollments": {"all": []}, "exposures": {"all": []}},
                "weekly": {
                    "enrollments": {
                        "all": WEEKLY_DATA,
                        "some_segment": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "variant": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    },
                    "exposures": {
                        "all": WEEKLY_DATA,
                        "some_segment": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "variant": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    },
                },
                "overall": {
                    "enrollments": {
                        "all": OVERALL_DATA,
                        "some_segment": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                            "percent": 50.0,
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "variant": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                            "percent": 50.0,
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    },
                    "exposures": {
                        "all": OVERALL_DATA,
                        "some_segment": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                            "percent": 50.0,
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "variant": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 10.0,
                                                        "point": 12.0,
                                                        "upper": 13.0,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 10.0,
                                                    "point": 12.0,
                                                    "upper": 13.0,
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                            "percent": 50.0,
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    },
                },
                "other_metrics": {
                    Group.OTHER.value: {
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
                                "custom_metric",
                            ],
                            "default_metrics": [],
                            "description": "default browser outcome",
                            "friendly_name": "Default Browser",
                            "slug": "default-browser",
                        }
                    },
                    "analysis_start_time": "2022-08-31T04:30:03+00:00",
                    "metrics": {},
                },
                "show_analysis": False,
                "errors": ERRORS,
            },
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
                                    "default_browser_null",
                                    "custom_metric"
                                ],
                                "default_metrics": [],
                                "description": "default browser outcome",
                                "friendly_name": "Default Browser",
                                "slug": "default-browser"
                            }
                        },
                        "analysis_start_time": "2022-08-31T04:30:03+00:00",
                        "metrics": {}
                    }"""
                if "errors" in self.name:
                    return """[
                        {
                            "exception": "(<class 'NoEnrollmentPeriodException'>)",
                            "exception_type": "NoEnrollmentPeriodException",
                            "experiment": "test-experiment-slug",
                            "filename": "cli.py",
                            "func_name": "execute",
                            "log_level": "ERROR",
                            "message": "test-experiment-slug -> error",
                            "metric": null,
                            "statistic": null,
                            "timestamp": "2022-08-31T04:32:03+00:00",
                            "analysis_basis": "enrollments",
                            "segment": "all"
                        },
                        {
                            "exception": "(<class 'NoEnrollmentPeriodException'>)",
                            "exception_type": "NoEnrollmentPeriodException",
                            "experiment": "test-experiment-slug",
                            "filename": "cli.py",
                            "func_name": "execute",
                            "log_level": "ERROR",
                            "message": "test-experiment-slug -> error",
                            "metric": null,
                            "statistic": null,
                            "timestamp": "2020-08-31T04:32:03+00:00",
                            "analysis_basis": "enrollments",
                            "segment": "all"
                        },
                        {
                            "exception": "(<class 'NoEnrollmentPeriodException'>)",
                            "exception_type": "NoEnrollmentPeriodException",
                            "experiment": "test-experiment-slug",
                            "filename": "cli.py",
                            "func_name": "execute",
                            "log_level": "ERROR",
                            "message": "test-experiment-slug -> error",
                            "metric": null,
                            "statistic": null,
                            "timestamp": "2022-08-31T04:32:04",
                            "analysis_basis": "enrollments",
                            "segment": "all"
                        },
                        {
                            "exception": "(<class 'NoEnrollmentPeriodException'>)",
                            "exception_type": "NoEnrollmentPeriodException",
                            "experiment": "test-experiment-slug",
                            "filename": "cli.py",
                            "func_name": "execute",
                            "log_level": "ERROR",
                            "message": "test-experiment-slug -> error",
                            "metric": null,
                            "statistic": null,
                            "timestamp": "2022-08-31T04:32:05",
                            "analysis_basis": "enrollments",
                            "segment": "all"
                        },
                        {
                            "exception": "(<class 'StatisticComputationException'>)",
                            "exception_type": "StatisticComputationException",
                            "experiment": "test-experiment-slug",
                            "filename": "statistics.py",
                            "func_name": "apply",
                            "log_level": "ERROR",
                            "message": "Error while computing statistic bootstrap_mean",
                            "metric": "default_browser_action",
                            "statistic": "bootstrap_mean",
                            "timestamp": "2022-08-31T04:32:03+00:00",
                            "analysis_basis": "enrollments",
                            "segment": "all"
                        },
                        {
                            "exception": "(<class 'StatisticComputationException'>)",
                            "exception_type": "StatisticComputationException",
                            "experiment": "test-experiment-slug",
                            "filename": "statistics.py",
                            "func_name": "apply",
                            "log_level": "ERROR",
                            "message": "Error while computing statistic binomial",
                            "metric": "spoc_tiles_disable_rate",
                            "statistic": "binomial",
                            "timestamp": "2022-08-31T04:32:03+00:00",
                            "analysis_basis": "enrollments",
                            "segment": "all"
                        }
                    ]"""
                return json.dumps(
                    DAILY_DATA
                    + SEGMENT_DATA
                    + DAILY_EXPOSURES_DATA
                    + SEGMENT_EXPOSURES_DATA
                )

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.results_data, FULL_DATA)

    @parameterized.expand(
        [
            (None, "2022-08-31T04:32:03"),
            ("", "2022-08-31 04:32:03+04:00"),
            ("2022-08-31T04:30:03+00:00", "2022-08-31T04:32:03+00:00"),
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_valid_error_and_analysis_timestamps(
        self, analysis_start_time, error_timestamp, mock_exists, mock_open
    ):
        experiment = NimbusExperimentFactory.create()

        (
            _,
            _,
            _,
            ERRORS,
            _,
            _,
            _,
        ) = JetstreamTestData.get_test_data([])

        FULL_DATA = {
            "v2": {
                "daily": {},
                "weekly": {},
                "overall": {},
                "metadata": {
                    "outcomes": {
                        "default-browser": {
                            "metrics": [
                                "default_browser_action",
                                "mozilla_default_browser",
                                "default_browser_null",
                                "custom_metric",
                            ],
                            "default_metrics": [],
                            "description": "default browser outcome",
                            "friendly_name": "Default Browser",
                            "slug": "default-browser",
                        }
                    },
                    "analysis_start_time": analysis_start_time,
                    "metrics": {},
                },
                "show_analysis": False,
                "errors": {
                    "experiment": [
                        {
                            "exception": "(<class 'NoEnrollmentPeriodException'>)",
                            "exception_type": "NoEnrollmentPeriodException",
                            "experiment": "test-experiment-slug",
                            "filename": "cli.py",
                            "func_name": "execute",
                            "log_level": "ERROR",
                            "message": "test-experiment-slug -> error",
                            "metric": None,
                            "statistic": None,
                            "timestamp": error_timestamp,
                            "analysis_basis": "enrollments",
                            "segment": "all",
                        }
                    ],
                },
            },
        }

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    ret_json = {
                        "outcomes": {
                            "default-browser": {
                                "metrics": [
                                    "default_browser_action",
                                    "mozilla_default_browser",
                                    "default_browser_null",
                                    "custom_metric",
                                ],
                                "default_metrics": [],
                                "description": "default browser outcome",
                                "friendly_name": "Default Browser",
                                "slug": "default-browser",
                            }
                        },
                        "analysis_start_time": analysis_start_time,
                        "metrics": {},
                    }
                elif "errors" in self.name:
                    ret_json = [
                        {
                            "exception": "(<class 'NoEnrollmentPeriodException'>)",
                            "exception_type": "NoEnrollmentPeriodException",
                            "experiment": "test-experiment-slug",
                            "filename": "cli.py",
                            "func_name": "execute",
                            "log_level": "ERROR",
                            "message": "test-experiment-slug -> error",
                            "metric": None,
                            "statistic": None,
                            "timestamp": error_timestamp,
                            "analysis_basis": "enrollments",
                            "segment": "all",
                        }
                    ]
                else:
                    ret_json = ""
                return json.dumps(ret_json)

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True

        if not error_timestamp:
            with self.assertRaises(Exception):
                tasks.fetch_experiment_data(experiment.id)
        else:
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
    def test_partial_exposures_results_data_parsed_and_stored(
        self, lifecycle, mock_exists, mock_open
    ):
        primary_outcomes = []
        secondary_outcomes = []
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
            ERRORS,
            SEGMENT_DATA,
            DAILY_EXPOSURES_DATA,
            SEGMENT_EXPOSURES_DATA,
            # WEEKLY_EXPOSURES_DATA,
            # WEEKLY_EXPOSURES_SEGMENT_DATA,
            # OVERALL_EXPOSURES_DATA,
            # OVERALL_EXPOSURES_SEGMENT_DATA,
        ) = JetstreamTestData.get_partial_exposures_test_data(primary_outcomes)

        FULL_DATA = {
            "v2": {
                "daily": {"enrollments": {"all": []}, "exposures": {"all": []}},
                "weekly": WEEKLY_DATA,
                "overall": OVERALL_DATA,
                "other_metrics": {
                    Group.OTHER.value: {
                        "some_count": "Some Count",
                        "another_count": "Another Count",
                    },
                },
                "metadata": {},
                "show_analysis": False,
                "errors": ERRORS,
            },
        }

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    return "{}"
                if "errors" in self.name:
                    return "[]"
                return json.dumps(
                    DAILY_DATA
                    + SEGMENT_DATA
                    + DAILY_EXPOSURES_DATA
                    + SEGMENT_EXPOSURES_DATA
                )

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.results_data, FULL_DATA)
        self.assertTrue(experiment.has_displayable_results)

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
            _,
            SEGMENT_DATA,
            _,
            _,
        ) = ZeroJetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "v2": {
                "daily": {"enrollments": {"all": []}},
                "weekly": {
                    "enrollments": {
                        "all": WEEKLY_DATA,
                        "some_segment": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.0,
                                                        "point": 0.0,
                                                        "upper": 0.0,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.0,
                                                    "point": 0.0,
                                                    "upper": 0.0,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "variant": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.0,
                                                        "point": 0.0,
                                                        "upper": 0.0,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.0,
                                                    "point": 0.0,
                                                    "upper": 0.0,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    },
                },
                "overall": {
                    "enrollments": {
                        "all": OVERALL_DATA,
                        "some_segment": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.0,
                                                        "point": 0.0,
                                                        "upper": 0.0,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.0,
                                                    "point": 0.0,
                                                    "upper": 0.0,
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                            "percent": 0.0,
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "variant": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.0,
                                                        "point": 0.0,
                                                        "upper": 0.0,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.0,
                                                    "point": 0.0,
                                                    "upper": 0.0,
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                            "percent": 0.0,
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    },
                },
                "other_metrics": {
                    Group.OTHER.value: {
                        "some_count": "Some Count",
                        "another_count": "Another Count",
                    },
                },
                "metadata": {},
                "show_analysis": False,
                "errors": {"experiment": []},
            },
        }

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    return "{}"
                return (
                    "[]"
                    if "errors" in self.name
                    else json.dumps(DAILY_DATA + SEGMENT_DATA)
                )

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.results_data, FULL_DATA)
        self.assertTrue(experiment.has_displayable_results)

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
            _,
            _,
            _,
            _,
            _,
            _,
        ) = NonePointJetstreamTestData.get_test_data(primary_outcomes)

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    return "{}"
                return "[]" if "errors" in self.name else json.dumps(DAILY_DATA)

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
    @patch("experimenter.jetstream.client.get_metadata")
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_with_pairwise_branch_comparisons(
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
        treatment_branch_a = experiment.treatment_branches[0]
        treatment_branch_a.slug = "treatment-a"
        treatment_branch_a.save()

        # raise ValueError(
        #     experiment.reference_branch.slug,
        #     [b.slug for b in experiment.treatment_branches],
        # )

        RESULTS_DATA = [
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-b",
                "comparison": "relative_uplift",
                "comparison_to_branch": "treatment-a",
                "ci_width": 0.95,
                "point": -0.1,
                "lower": -0.2,
                "upper": -0.01,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-b",
                "comparison": "relative_uplift",
                "comparison_to_branch": "control",
                "ci_width": 0.95,
                "point": 0.1,
                "lower": 2.2,
                "upper": 0.02,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-b",
                "comparison": "difference",
                "comparison_to_branch": "treatment-a",
                "ci_width": 0.95,
                "point": -0.8,
                "lower": -0.9,
                "upper": -0.5,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-b",
                "comparison": "difference",
                "comparison_to_branch": "control",
                "ci_width": 0.95,
                "point": 0.0,
                "lower": 1.0,
                "upper": 0.5,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-b",
                "ci_width": 0.95,
                "point": 0.857,
                "lower": 0.856,
                "upper": 0.8589,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-a",
                "comparison": "relative_uplift",
                "comparison_to_branch": "treatment-b",
                "ci_width": 0.95,
                "point": 0.11111111111111111111,
                "lower": 3.14159265358979323846,
                "upper": 0.22222222222222222222,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-a",
                "comparison": "relative_uplift",
                "comparison_to_branch": "control",
                "ci_width": 0.95,
                "point": 0.2,
                "lower": 0.1,
                "upper": 0.3,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-a",
                "comparison": "difference",
                "comparison_to_branch": "treatment-b",
                "ci_width": 0.95,
                "point": 0.1,
                "lower": 2.5,
                "upper": 1.0,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-a",
                "comparison": "difference",
                "comparison_to_branch": "control",
                "ci_width": 0.95,
                "point": 0.1,
                "lower": -10.0,
                "upper": 10.2,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "treatment-a",
                "ci_width": 0.95,
                "point": 0.858,
                "lower": 0.857,
                "upper": 0.8596,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "control",
                "comparison": "relative_uplift",
                "comparison_to_branch": "treatment-b",
                "ci_width": 0.95,
                "point": -2.1,
                "lower": -2.2,
                "upper": -2.01,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "control",
                "comparison": "relative_uplift",
                "comparison_to_branch": "treatment-a",
                "ci_width": 0.95,
                "point": -0.2,
                "lower": -0.3,
                "upper": -0.1,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "control",
                "comparison": "difference",
                "comparison_to_branch": "treatment-b",
                "ci_width": 0.95,
                "point": -1.1,
                "lower": -1.2,
                "upper": -1.01,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "control",
                "comparison": "difference",
                "comparison_to_branch": "treatment-a",
                "ci_width": 0.95,
                "point": -0.1,
                "lower": -10.2,
                "upper": -0.01,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
            {
                "metric": "test",
                "statistic": "binomial",
                "branch": "control",
                "ci_width": 0.95,
                "point": 0.856,
                "lower": 0.855,
                "upper": 0.8575,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "1",
            },
        ]

        FULL_DATA = {
            "v2": {
                "daily": {"enrollments": {"all": []}},
                "weekly": {
                    "enrollments": {
                        "all": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "test": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.855,
                                                        "point": 0.856,
                                                        "upper": 0.8575,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.855,
                                                    "point": 0.856,
                                                    "upper": 0.8575,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -10.2,
                                                            "point": -0.1,
                                                            "upper": -0.01,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -10.2,
                                                        "point": -0.1,
                                                        "upper": -0.01,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": -1.2,
                                                            "point": -1.1,
                                                            "upper": -1.01,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -1.2,
                                                        "point": -1.1,
                                                        "upper": -1.01,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "control": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -0.3,
                                                            "point": -0.2,
                                                            "upper": -0.1,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -0.3,
                                                        "point": -0.2,
                                                        "upper": -0.1,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": -2.2,
                                                            "point": -2.1,
                                                            "upper": -2.01,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -2.2,
                                                        "point": -2.1,
                                                        "upper": -2.01,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "control": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {"1": "negative"},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {"1": "negative"},
                                                },
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "treatment-a": {
                                "branch_data": {
                                    "other_metrics": {
                                        "test": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.857,
                                                        "point": 0.858,
                                                        "upper": 0.8596,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.857,
                                                    "point": 0.858,
                                                    "upper": 0.8596,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [
                                                    {
                                                        "lower": -10.0,
                                                        "point": 0.1,
                                                        "upper": 10.2,
                                                        "window_index": "1",
                                                    },
                                                ],
                                                "first": {
                                                    "lower": -10.0,
                                                    "point": 0.1,
                                                    "upper": 10.2,
                                                    "window_index": "1",
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": -10.0,
                                                            "point": 0.1,
                                                            "upper": 10.2,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -10.0,
                                                        "point": 0.1,
                                                        "upper": 10.2,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": 2.5,
                                                            "point": 0.1,
                                                            "upper": 1.0,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 2.5,
                                                        "point": 0.1,
                                                        "upper": 1.0,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "all": [
                                                    {
                                                        "lower": 0.1,
                                                        "point": 0.2,
                                                        "upper": 0.3,
                                                        "window_index": "1",
                                                    },
                                                ],
                                                "first": {
                                                    "lower": 0.1,
                                                    "point": 0.2,
                                                    "upper": 0.3,
                                                    "window_index": "1",
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 0.1,
                                                            "point": 0.2,
                                                            "upper": 0.3,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 0.1,
                                                        "point": 0.2,
                                                        "upper": 0.3,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": 3.141592653589793,
                                                            "point": 0.1111111111111111,
                                                            "upper": 0.2222222222222222,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 3.141592653589793,
                                                        "point": 0.1111111111111111,
                                                        "upper": 0.2222222222222222,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {"1": "neutral"},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {"1": "neutral"},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {"1": "positive"},
                                                },
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                            "treatment-b": {
                                "branch_data": {
                                    "other_metrics": {
                                        "test": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.856,
                                                        "point": 0.857,
                                                        "upper": 0.8589,
                                                        "window_index": "1",
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.856,
                                                    "point": 0.857,
                                                    "upper": 0.8589,
                                                    "window_index": "1",
                                                },
                                            },
                                            "difference": {
                                                "all": [
                                                    {
                                                        "lower": 1.0,
                                                        "point": 0.0,
                                                        "upper": 0.5,
                                                        "window_index": "1",
                                                    },
                                                ],
                                                "first": {
                                                    "lower": 1.0,
                                                    "point": 0.0,
                                                    "upper": 0.5,
                                                    "window_index": "1",
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 1.0,
                                                            "point": 0.0,
                                                            "upper": 0.5,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 1.0,
                                                        "point": 0.0,
                                                        "upper": 0.5,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -0.9,
                                                            "point": -0.8,
                                                            "upper": -0.5,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -0.9,
                                                        "point": -0.8,
                                                        "upper": -0.5,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "all": [
                                                    {
                                                        "lower": 2.2,
                                                        "point": 0.1,
                                                        "upper": 0.02,
                                                        "window_index": "1",
                                                    },
                                                ],
                                                "first": {
                                                    "lower": 2.2,
                                                    "point": 0.1,
                                                    "upper": 0.02,
                                                    "window_index": "1",
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 2.2,
                                                            "point": 0.1,
                                                            "upper": 0.02,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 2.2,
                                                        "point": 0.1,
                                                        "upper": 0.02,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -0.2,
                                                            "point": -0.1,
                                                            "upper": -0.01,
                                                            "window_index": "1",
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -0.2,
                                                        "point": -0.1,
                                                        "upper": -0.01,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {"1": "positive"},
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {"1": "positive"},
                                                },
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {"1": "negative"},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    }
                },
                "overall": {
                    "enrollments": {
                        "all": {
                            "control": {
                                "branch_data": {
                                    "other_metrics": {
                                        "test": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.855,
                                                        "point": 0.856,
                                                        "upper": 0.8575,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.855,
                                                    "point": 0.856,
                                                    "upper": 0.8575,
                                                },
                                            },
                                            "difference": {
                                                "all": [],
                                                "first": {},
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -10.2,
                                                            "point": -0.1,
                                                            "upper": -0.01,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -10.2,
                                                        "point": -0.1,
                                                        "upper": -0.01,
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": -1.2,
                                                            "point": -1.1,
                                                            "upper": -1.01,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -1.2,
                                                        "point": -1.1,
                                                        "upper": -1.01,
                                                    },
                                                },
                                                "control": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "all": [],
                                                "first": {},
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -0.3,
                                                            "point": -0.2,
                                                            "upper": -0.1,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -0.3,
                                                        "point": -0.2,
                                                        "upper": -0.1,
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": -2.2,
                                                            "point": -2.1,
                                                            "upper": -2.01,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -2.2,
                                                        "point": -2.1,
                                                        "upper": -2.01,
                                                    },
                                                },
                                                "control": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "significance": {
                                                "overall": {},
                                                "weekly": {},
                                                "treatment-a": {
                                                    "overall": {"1": "negative"},
                                                    "weekly": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {"1": "negative"},
                                                    "weekly": {},
                                                },
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": True,
                            },
                            "treatment-a": {
                                "branch_data": {
                                    "other_metrics": {
                                        "test": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.857,
                                                        "point": 0.858,
                                                        "upper": 0.8596,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.857,
                                                    "point": 0.858,
                                                    "upper": 0.8596,
                                                },
                                            },
                                            "difference": {
                                                "all": [
                                                    {
                                                        "lower": -10.0,
                                                        "point": 0.1,
                                                        "upper": 10.2,
                                                    },
                                                ],
                                                "first": {
                                                    "lower": -10.0,
                                                    "point": 0.1,
                                                    "upper": 10.2,
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": -10.0,
                                                            "point": 0.1,
                                                            "upper": 10.2,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -10.0,
                                                        "point": 0.1,
                                                        "upper": 10.2,
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": 2.5,
                                                            "point": 0.1,
                                                            "upper": 1.0,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 2.5,
                                                        "point": 0.1,
                                                        "upper": 1.0,
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "all": [
                                                    {
                                                        "lower": 0.1,
                                                        "point": 0.2,
                                                        "upper": 0.3,
                                                    },
                                                ],
                                                "first": {
                                                    "lower": 0.1,
                                                    "point": 0.2,
                                                    "upper": 0.3,
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 0.1,
                                                            "point": 0.2,
                                                            "upper": 0.3,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 0.1,
                                                        "point": 0.2,
                                                        "upper": 0.3,
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": 3.141592653589793,
                                                            "point": 0.1111111111111111,
                                                            "upper": 0.2222222222222222,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 3.141592653589793,
                                                        "point": 0.1111111111111111,
                                                        "upper": 0.2222222222222222,
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "significance": {
                                                "overall": {"1": "neutral"},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {"1": "neutral"},
                                                    "weekly": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {"1": "positive"},
                                                    "weekly": {},
                                                },
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                            "treatment-b": {
                                "branch_data": {
                                    "other_metrics": {
                                        "test": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 0.856,
                                                        "point": 0.857,
                                                        "upper": 0.8589,
                                                    }
                                                ],
                                                "first": {
                                                    "lower": 0.856,
                                                    "point": 0.857,
                                                    "upper": 0.8589,
                                                },
                                            },
                                            "difference": {
                                                "all": [
                                                    {
                                                        "lower": 1.0,
                                                        "point": 0.0,
                                                        "upper": 0.5,
                                                    },
                                                ],
                                                "first": {
                                                    "lower": 1.0,
                                                    "point": 0.0,
                                                    "upper": 0.5,
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 1.0,
                                                            "point": 0.0,
                                                            "upper": 0.5,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 1.0,
                                                        "point": 0.0,
                                                        "upper": 0.5,
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -0.9,
                                                            "point": -0.8,
                                                            "upper": -0.5,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -0.9,
                                                        "point": -0.8,
                                                        "upper": -0.5,
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "all": [
                                                    {
                                                        "lower": 2.2,
                                                        "point": 0.1,
                                                        "upper": 0.02,
                                                    },
                                                ],
                                                "first": {
                                                    "lower": 2.2,
                                                    "point": 0.1,
                                                    "upper": 0.02,
                                                },
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 2.2,
                                                            "point": 0.1,
                                                            "upper": 0.02,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": 2.2,
                                                        "point": 0.1,
                                                        "upper": 0.02,
                                                    },
                                                },
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -0.2,
                                                            "point": -0.1,
                                                            "upper": -0.01,
                                                        },
                                                    ],
                                                    "first": {
                                                        "lower": -0.2,
                                                        "point": -0.1,
                                                        "upper": -0.01,
                                                    },
                                                },
                                                "treatment-b": {
                                                    "all": [],
                                                    "first": {},
                                                },
                                            },
                                            "significance": {
                                                "overall": {"1": "positive"},
                                                "weekly": {},
                                                "control": {
                                                    "overall": {"1": "positive"},
                                                    "weekly": {},
                                                },
                                                "treatment-a": {
                                                    "overall": {"1": "negative"},
                                                    "weekly": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {},
                                                },
                                            },
                                        }
                                    },
                                    "search_metrics": {},
                                    "usage_metrics": {},
                                },
                                "is_control": False,
                            },
                        },
                    }
                },
                "errors": {"experiment": []},
                "metadata": {
                    "outcomes": {
                        "default-browser": {"default_metrics": [], "metrics": ["test"]}
                    }
                },
                "other_metrics": {"other_metrics": {"test": "Test"}},
                "show_analysis": False,
            }
        }

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    return "{}"
                return "[]" if "errors" in self.name else json.dumps(RESULTS_DATA)

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
        self.assertEqual(experiment.results_data, FULL_DATA)

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
                "v2": {
                    "daily": {},
                    "metadata": None,
                    "overall": {},
                    "show_analysis": False,
                    "weekly": {},
                    "errors": {"experiment": []},
                },
            },
        )
        self.assertFalse(experiment.has_displayable_results)

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_in_loop(self, mock_delay):
        lifecycle = NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_live_continue_fetching_after_proposed_end(self, mock_delay):
        lifecycle = NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, start_date=datetime.date(2020, 1, 1), proposed_enrollment=12
        )
        experiment.results_data = {}
        experiment.save()

        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_skip_old_complete(self, mock_delay):
        lifecycle = NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, start_date=datetime.date(2020, 1, 1), proposed_enrollment=12
        )
        experiment.results_data = {}
        experiment.save()

        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_skip_preview(self, mock_delay):
        lifecycle = NimbusExperimentFactory.Lifecycles.PREVIEW
        offset = NimbusExperiment.DAYS_ANALYSIS_BUFFER + 1
        _ = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=offset)
        )
        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_expired_in_loop(self, mock_delay):
        lifecycle = NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        offset = NimbusExperiment.DAYS_ANALYSIS_BUFFER + 1
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=offset)
        )
        experiment.results_data = {
            "v2": {
                "daily": None,
                "metadata": None,
                "overall": None,
                "show_analysis": False,
                "weekly": None,
            },
        }
        experiment.save()

        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_null_fetches(self, mock_delay):
        lifecycle = NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        offset = NimbusExperiment.DAYS_ANALYSIS_BUFFER + 1
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=offset)
        )

        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_no_data_fetch_in_loop(self, mock_delay):
        lifecycle = NimbusExperimentFactory.Lifecycles.CREATED
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

    @patch("experimenter.jetstream.client.validate_data")
    @patch("experimenter.jetstream.client.load_data_from_gcs")
    def test_builds_statistics_filename(
        self, mock_load_data_from_gcs, mock_validate_data
    ):
        lifecycle = NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        offset = NimbusExperiment.DAYS_ANALYSIS_BUFFER + 1
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=offset)
        )

        mock_validate_data.return_value = True

        recipe_slug = experiment.slug.replace("-", "_")
        window = AnalysisWindow.OVERALL
        get_data(recipe_slug, AnalysisWindow.OVERALL)
        filename = f"statistics/statistics_{recipe_slug}_{window}.json"
        mock_load_data_from_gcs.assert_called_with(filename)

        assert "AnalysisWindow" not in filename
        assert "overall" in filename

    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_sizing_data_parsed_and_stored(self, mock_exists, mock_open):
        sizing_test_data = SampleSizesFactory.build().json()

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                return "" if "sample_sizes" not in self.name else sizing_test_data

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True

        sizing_results = cache.get(SIZING_DATA_KEY)
        self.assertIsNone(sizing_results)

        tasks.fetch_population_sizing_data()
        sizing_results = cache.get(SIZING_DATA_KEY)

        self.assertEqual(
            json.dumps(json.loads(sizing_test_data)),
            sizing_results.json(exclude_unset=True),
        )

    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_empty_fetch_population_sizing_data(self, mock_exists, mock_open):
        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                return "" if "sample_sizes" not in self.name else "{}"

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True

        sizing_results = cache.get(SIZING_DATA_KEY)
        self.assertIsNone(sizing_results)

        tasks.fetch_population_sizing_data()
        sizing_results = cache.get(SIZING_DATA_KEY)
        self.assertEqual(sizing_results.json(), "{}")

    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_fetch_population_sizing_data_invalid(self, mock_exists, mock_open):
        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "sample_sizes" not in self.name:
                    return ""
                return """
                    {"test": {"invalid_key"}}
                """

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True
        with self.assertRaises(Exception):
            tasks.fetch_population_sizing_data()
