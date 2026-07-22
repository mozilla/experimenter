import datetime
import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from mozilla_nimbus_schemas.jetstream import SampleSizes, SampleSizesFactory
from parameterized import parameterized

from experimenter.experiments.constants import APPLICATION_CONFIG_DESKTOP
from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.jetstream import tasks
from experimenter.jetstream.client import (
    ERRORS_FOLDER,
    METADATA_FOLDER,
    STATISTICS_FOLDER,
    expected_windows,
    get_data,
    get_enrollment_funnel_data,
    get_featmon_slugs,
    get_latest_analysis_start_time,
    get_monitoring_data,
    get_results_filenames,
    get_stored_analysis_start_time,
    has_missing_expected_results,
)
from experimenter.jetstream.models import AnalysisWindow, Group, Metric
from experimenter.jetstream.tests import mock_valid_outcomes
from experimenter.jetstream.tests.constants import (
    JetstreamTestData,
    NonePointJetstreamTestData,
    ZeroJetstreamTestData,
)
from experimenter.jetstream.tests.mixins import MockSizingDataMixin
from experimenter.outcomes import Outcomes


@mock_valid_outcomes
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
    def test_valid_results_data_parsed_and_stored(self, lifecycle):
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
            FORMATTED_DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
            ERRORS,
            SEGMENT_DATA,
            DAILY_EXPOSURES_DATA,
            SEGMENT_EXPOSURES_DATA,
        ) = JetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "v3": {
                "daily": {
                    "enrollments": {
                        "all": FORMATTED_DAILY_DATA,
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                        "all": FORMATTED_DAILY_DATA,
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                        "some_dau_impact": "Some Dau Impact",
                        "some_ratio": "Some Ratio",
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

        with (
            patch("experimenter.jetstream.client.analysis_storage.open") as mock_open,
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
        ):
            mock_open.side_effect = open_file
            mock_exists.return_value = True

            tasks.fetch_experiment_data(experiment.id)
            experiment = NimbusExperiment.objects.get(id=experiment.id)
            self.assertEqual(experiment.results_data, FULL_DATA)
            self.assertEqual(
                experiment.changes.filter(
                    message=NimbusChangeLog.Messages.RESULTS_UPDATED
                ).count(),
                1,
            )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_no_changelog_when_only_timestamps_changed(self, lifecycle):
        primary_outcomes = ["default-browser"]
        secondary_outcomes = ["secondary_outcome"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
            secondary_outcomes=secondary_outcomes,
        )

        old_data = {
            "v3": {
                "errors": {
                    "experiment": [
                        {
                            "metric": None,
                            "message": "Could not find data",
                            "timestamp": "2025-12-17T02:00:47.111Z",
                            "experiment": "test-experiment",
                        }
                    ]
                },
                "weekly": {},
                "overall": {},
                "metadata": None,
            }
        }

        new_data = {
            "v3": {
                "errors": {
                    "experiment": [
                        {
                            "metric": None,
                            "message": "Could not find data",
                            "timestamp": "2025-12-17T04:00:47.764Z",
                            "experiment": "test-experiment",
                        }
                    ]
                },
                "weekly": {},
                "overall": {},
                "metadata": None,
            }
        }

        experiment.results_data = old_data
        experiment.save()

        initial_changelog_count = experiment.changes.filter(
            message=NimbusChangeLog.Messages.RESULTS_UPDATED
        ).count()

        with patch(
            "experimenter.jetstream.tasks.get_experiment_data"
        ) as mock_get_experiment_data:
            mock_get_experiment_data.return_value = new_data

            tasks.fetch_experiment_data(experiment.id)
            experiment = NimbusExperiment.objects.get(id=experiment.id)

            self.assertEqual(experiment.results_data, new_data)

            final_changelog_count = experiment.changes.filter(
                message=NimbusChangeLog.Messages.RESULTS_UPDATED
            ).count()
            self.assertEqual(final_changelog_count, initial_changelog_count)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_no_changelog_when_results_data_unchanged(self, lifecycle):
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
            _,
            _,
            WEEKLY_DATA,
            OVERALL_DATA,
            ERRORS,
            _,
            _,
            _,
        ) = JetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "v3": {
                "weekly": {
                    "enrollments": {
                        "all": WEEKLY_DATA,
                    },
                },
                "overall": {
                    "enrollments": {
                        "all": OVERALL_DATA,
                    },
                },
                "other_metrics": {
                    Group.OTHER.value: {
                        "some_count": "Some Count",
                    },
                },
                "metadata": {},
                "errors": ERRORS,
            },
        }

        experiment.results_data = FULL_DATA
        experiment.save()

        initial_changelog_count = experiment.changes.filter(
            message=NimbusChangeLog.Messages.RESULTS_UPDATED
        ).count()

        with patch(
            "experimenter.jetstream.tasks.get_experiment_data"
        ) as mock_get_experiment_data:
            mock_get_experiment_data.return_value = FULL_DATA

            tasks.fetch_experiment_data(experiment.id)
            experiment = NimbusExperiment.objects.get(id=experiment.id)

            self.assertEqual(experiment.results_data, FULL_DATA)

            final_changelog_count = experiment.changes.filter(
                message=NimbusChangeLog.Messages.RESULTS_UPDATED
            ).count()
            self.assertEqual(final_changelog_count, initial_changelog_count)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_complete_results_data_missing_weekly(self, lifecycle):
        primary_outcomes = ["default-browser"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
        )

        def mock_jetstream_data_by_window(_, window):
            if window == AnalysisWindow.DAILY:
                return [
                    {
                        "metric": "identity",
                        "statistic": "count",
                        "branch": "control",
                        "point": 10,
                        "segment": "all",
                        "analysis_basis": "enrollments",
                        "window_index": "1",
                    },
                    {
                        "metric": "identity",
                        "statistic": "count",
                        "branch": "control",
                        "point": 20,
                        "segment": "all",
                        "analysis_basis": "enrollments",
                        "window_index": "2",
                    },
                ]
            elif window == AnalysisWindow.WEEKLY:
                return []  # Simulate missing weekly data
            elif window == AnalysisWindow.OVERALL:
                return [
                    {
                        "metric": "identity",
                        "statistic": "count",
                        "branch": "control",
                        "point": 40,
                        "segment": "all",
                        "analysis_basis": "enrollments",
                        "window_index": "1",
                    }
                ]
            return []

        with (
            patch("experimenter.jetstream.client.get_data") as mock_get_data,
            patch("experimenter.jetstream.client.get_metadata") as mock_get_metadata,
            patch("experimenter.jetstream.client.get_analysis_errors") as mock_get_errors,
        ):
            mock_get_data.side_effect = mock_jetstream_data_by_window
            mock_get_metadata.return_value = None
            mock_get_errors.return_value = None
            tasks.fetch_experiment_data(experiment.id)

    def test_results_data_warns_when_week_2_retention_is_missing(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        experiment.reference_branch.slug = "control"
        experiment.reference_branch.save()

        def mock_jetstream_data_by_window(_, window):
            if window == AnalysisWindow.WEEKLY:
                return [
                    {
                        "metric": Metric.RETENTION,
                        "statistic": "binomial",
                        "branch": "control",
                        "point": 0.5,
                        "segment": "all",
                        "analysis_basis": "enrollments",
                        "window_index": "1",
                    }
                ]
            if window == AnalysisWindow.OVERALL:
                return [
                    {
                        "metric": "identity",
                        "statistic": "count",
                        "branch": "control",
                        "point": 10,
                        "segment": "all",
                        "analysis_basis": "enrollments",
                        "window_index": "1",
                    }
                ]
            return []

        with (
            patch("experimenter.jetstream.client.get_data") as mock_get_data,
            patch("experimenter.jetstream.client.get_metadata") as mock_get_metadata,
            patch("experimenter.jetstream.client.get_analysis_errors") as mock_get_errors,
        ):
            mock_get_data.side_effect = mock_jetstream_data_by_window
            mock_get_metadata.return_value = None
            mock_get_errors.return_value = None

            tasks.fetch_experiment_data(experiment.id)

        experiment.refresh_from_db()
        errors = experiment.results_data["v3"]["errors"]["experiment"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["metric"], Metric.RETENTION)
        self.assertEqual(
            errors[0]["message"],
            "Week 2 retention is unavailable because this experiment did not run "
            "long enough.",
        )

    @parameterized.expand(
        [
            (None, "2022-08-31T04:32:03"),
            ("", "2022-08-31 04:32:03+04:00"),
            ("2022-08-31T04:30:03+00:00", "2022-08-31T04:32:03+00:00"),
        ]
    )
    def test_valid_error_and_analysis_timestamps(
        self,
        analysis_start_time,
        error_timestamp,
    ):
        experiment = NimbusExperimentFactory.create()

        (
            _,
            _,
            _,
            _,
            ERRORS,
            _,
            _,
            _,
        ) = JetstreamTestData.get_test_data([])

        FULL_DATA = {
            "v3": {
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

        with (
            patch("experimenter.jetstream.client.analysis_storage.open") as mock_open,
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
        ):
            mock_open.side_effect = open_file
            mock_exists.return_value = True

            if not error_timestamp:
                with self.assertRaises(Exception):
                    tasks.fetch_experiment_data(experiment.id)
            else:
                tasks.fetch_experiment_data(experiment.id)
                experiment = NimbusExperiment.objects.get(id=experiment.id)
                self.assertEqual(experiment.results_data, FULL_DATA)

    def test_metric_errors_before_analysis_start_time_are_excluded(self):
        experiment = NimbusExperimentFactory.create(
            primary_outcomes=[],
            secondary_outcomes=[],
        )
        fresh_error = {
            "exception": "(<class 'MetricException'>)",
            "exception_type": "MetricException",
            "experiment": "test-experiment-slug",
            "filename": "metrics.py",
            "func_name": "execute",
            "log_level": "ERROR",
            "message": "test-experiment-slug -> metric error",
            "metric": "custom_metric",
            "statistic": None,
            "timestamp": "2026-05-19T04:30:03+00:00",
            "analysis_basis": "enrollments",
            "segment": "all",
        }
        stale_error = {
            "exception": "(<class 'MetricException'>)",
            "exception_type": "MetricException",
            "experiment": "test-experiment-slug",
            "filename": "metrics.py",
            "func_name": "execute",
            "log_level": "ERROR",
            "message": "test-experiment-slug -> stale metric error",
            "metric": "custom_metric",
            "statistic": None,
            "timestamp": "2026-05-17T04:30:03+00:00",
            "analysis_basis": "enrollments",
            "segment": "all",
        }
        malformed_error = {
            "exception": "(<class 'MetricException'>)",
            "exception_type": "MetricException",
            "experiment": "test-experiment-slug",
            "filename": "metrics.py",
            "func_name": "execute",
            "log_level": "ERROR",
            "message": "test-experiment-slug -> malformed metric error",
            "metric": "malformed_metric",
            "statistic": None,
            "timestamp": "not-a-date",
            "analysis_basis": "enrollments",
            "segment": "all",
        }

        with (
            patch("experimenter.jetstream.client.get_data") as mock_get_data,
            patch("experimenter.jetstream.client.get_metadata") as mock_get_metadata,
            patch("experimenter.jetstream.client.get_analysis_errors") as mock_get_errors,
        ):
            mock_get_data.return_value = []
            mock_get_metadata.return_value = {
                "analysis_start_time": "2026-05-18T04:30:03+00:00",
                "outcomes": {},
                "metrics": {},
            }
            mock_get_errors.return_value = [fresh_error, stale_error, malformed_error]
            tasks.fetch_experiment_data(experiment.id)
            experiment = NimbusExperiment.objects.get(id=experiment.id)

            self.assertEqual(
                experiment.results_data["v3"]["errors"],
                {
                    "custom_metric": [fresh_error],
                    "malformed_metric": [malformed_error],
                    "experiment": [],
                },
            )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_partial_exposures_results_data_parsed_and_stored(self, lifecycle):
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
            FORMATTED_DAILY_DATA,
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
            "v3": {
                "daily": FORMATTED_DAILY_DATA,
                "weekly": WEEKLY_DATA,
                "overall": OVERALL_DATA,
                "other_metrics": {
                    Group.OTHER.value: {
                        "some_count": "Some Count",
                        "another_count": "Another Count",
                    },
                },
                "metadata": {},
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

        with (
            patch("experimenter.jetstream.client.analysis_storage.open") as mock_open,
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
        ):
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
    def test_results_data_with_zeros_parsed_and_stored(
        self,
        lifecycle,
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
            FORMATTED_DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
            _,
            SEGMENT_DATA,
            _,
            _,
        ) = ZeroJetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "v3": {
                "daily": {
                    "enrollments": {
                        "all": FORMATTED_DAILY_DATA,
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "variant": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "variant": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                        "some_dau_impact": "Some Dau Impact",
                        "some_ratio": "Some Ratio",
                    },
                },
                "metadata": {},
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

        with (
            patch("experimenter.jetstream.client.analysis_storage.open") as mock_open,
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
        ):
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
    def test_results_data_with_null_conversion_percent(
        self, lifecycle, mock_get_metadata
    ):
        primary_outcomes = ["default-browser"]
        secondary_outcomes = ["secondary_outcome"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
            secondary_outcomes=secondary_outcomes,
            results_data=None,
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

        with (
            patch("experimenter.jetstream.client.analysis_storage.open") as mock_open,
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
        ):
            mock_open.side_effect = open_file
            mock_exists.return_value = True

            experiment = NimbusExperiment.objects.get(id=experiment.id)
            self.assertIsNone(experiment.results_data)

            mock_get_metadata.return_value = {
                "outcomes": {
                    "default-browser": {"metrics": ["test"], "default_metrics": []}
                }
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
    def test_results_data_with_pairwise_branch_comparisons(
        self, lifecycle, mock_get_metadata
    ):
        primary_outcomes = ["default-browser"]
        secondary_outcomes = ["secondary_outcome"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
            secondary_outcomes=secondary_outcomes,
            results_data=None,
        )
        experiment.reference_branch.slug = "control"
        experiment.reference_branch.save()
        treatment_branch_a = experiment.treatment_branches[0]
        treatment_branch_a.slug = "treatment-a"
        treatment_branch_a.save()

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
            "v3": {
                "daily": {
                    "enrollments": {
                        "all": {
                            "control": {
                                "is_control": True,
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
                                                "control": {"all": [], "first": {}},
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -10.2,
                                                            "point": -0.1,
                                                            "upper": -0.01,
                                                            "window_index": "1",
                                                        }
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
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": -1.2,
                                                        "point": -1.1,
                                                        "upper": -1.01,
                                                        "window_index": "1",
                                                    },
                                                },
                                            },
                                            "significance": {
                                                "control": {
                                                    "daily": {},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                                "treatment-a": {
                                                    "daily": {"1": "negative"},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                                "treatment-b": {
                                                    "daily": {"1": "negative"},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}},
                                                "treatment-a": {
                                                    "all": [
                                                        {
                                                            "lower": -0.3,
                                                            "point": -0.2,
                                                            "upper": -0.1,
                                                            "window_index": "1",
                                                        }
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
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": -2.2,
                                                        "point": -2.1,
                                                        "upper": -2.01,
                                                        "window_index": "1",
                                                    },
                                                },
                                            },
                                        }
                                    },
                                    "usage_metrics": {},
                                    "search_metrics": {},
                                },
                            },
                            "treatment-a": {
                                "is_control": False,
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
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": -10.0,
                                                            "point": 0.1,
                                                            "upper": 10.2,
                                                            "window_index": "1",
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": -10.0,
                                                        "point": 0.1,
                                                        "upper": 10.2,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-a": {"all": [], "first": {}},
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": 2.5,
                                                            "point": 0.1,
                                                            "upper": 1.0,
                                                            "window_index": "1",
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": 2.5,
                                                        "point": 0.1,
                                                        "upper": 1.0,
                                                        "window_index": "1",
                                                    },
                                                },
                                            },
                                            "significance": {
                                                "control": {
                                                    "daily": {"1": "neutral"},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                                "treatment-a": {
                                                    "daily": {},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                                "treatment-b": {
                                                    "daily": {"1": "positive"},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 0.1,
                                                            "point": 0.2,
                                                            "upper": 0.3,
                                                            "window_index": "1",
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": 0.1,
                                                        "point": 0.2,
                                                        "upper": 0.3,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-a": {"all": [], "first": {}},
                                                "treatment-b": {
                                                    "all": [
                                                        {
                                                            "lower": 3.141592653589793,
                                                            "point": 0.1111111111111111,
                                                            "upper": 0.2222222222222222,
                                                            "window_index": "1",
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": 3.141592653589793,
                                                        "point": 0.1111111111111111,
                                                        "upper": 0.2222222222222222,
                                                        "window_index": "1",
                                                    },
                                                },
                                            },
                                        }
                                    },
                                    "usage_metrics": {},
                                    "search_metrics": {},
                                },
                            },
                            "treatment-b": {
                                "is_control": False,
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
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 1.0,
                                                            "point": 0.0,
                                                            "upper": 0.5,
                                                            "window_index": "1",
                                                        }
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
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": -0.9,
                                                        "point": -0.8,
                                                        "upper": -0.5,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {"all": [], "first": {}},
                                            },
                                            "significance": {
                                                "control": {
                                                    "daily": {"1": "positive"},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                                "treatment-a": {
                                                    "daily": {"1": "negative"},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                                "treatment-b": {
                                                    "daily": {},
                                                    "weekly": {},
                                                    "overall": {},
                                                },
                                            },
                                            "relative_uplift": {
                                                "control": {
                                                    "all": [
                                                        {
                                                            "lower": 2.2,
                                                            "point": 0.1,
                                                            "upper": 0.02,
                                                            "window_index": "1",
                                                        }
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
                                                        }
                                                    ],
                                                    "first": {
                                                        "lower": -0.2,
                                                        "point": -0.1,
                                                        "upper": -0.01,
                                                        "window_index": "1",
                                                    },
                                                },
                                                "treatment-b": {"all": [], "first": {}},
                                            },
                                        }
                                    },
                                    "usage_metrics": {},
                                    "search_metrics": {},
                                },
                            },
                        }
                    }
                },
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
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {"1": "negative"},
                                                    "daily": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {"1": "negative"},
                                                    "daily": {},
                                                },
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {"1": "neutral"},
                                                    "daily": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {"1": "positive"},
                                                    "daily": {},
                                                },
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {"1": "positive"},
                                                    "daily": {},
                                                },
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {"1": "negative"},
                                                    "daily": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "treatment-a": {
                                                    "overall": {"1": "negative"},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {"1": "negative"},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "control": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {
                                                    "overall": {"1": "neutral"},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {"1": "positive"},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "treatment-a": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
                                                "control": {
                                                    "overall": {"1": "positive"},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "treatment-a": {
                                                    "overall": {"1": "negative"},
                                                    "weekly": {},
                                                    "daily": {},
                                                },
                                                "treatment-b": {
                                                    "overall": {},
                                                    "weekly": {},
                                                    "daily": {},
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
            },
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

        with (
            patch("experimenter.jetstream.client.analysis_storage.open") as mock_open,
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
        ):
            mock_open.side_effect = open_file
            mock_exists.return_value = True

            experiment = NimbusExperiment.objects.get(id=experiment.id)
            self.assertIsNone(experiment.results_data)

            mock_get_metadata.return_value = {
                "outcomes": {
                    "default-browser": {"metrics": ["test"], "default_metrics": []}
                }
            }

            tasks.fetch_experiment_data(experiment.id)
            experiment = NimbusExperiment.objects.get(id=experiment.id)
            self.assertEqual(experiment.results_data, FULL_DATA)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED, 1),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE, 1),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE, 2),
        ]
    )
    def test_results_data_null(self, lifecycle, offset):
        primary_outcome = "default-browser"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=[primary_outcome],
            end_date=datetime.date.today() - datetime.timedelta(days=offset),
        )

        now = timezone.now()

        with (
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
            patch("experimenter.jetstream.client.timezone") as mock_timezone,
        ):
            mock_exists.return_value = False
            mock_timezone.now.return_value = now

            experiment_errors = [
                {
                    "analysis_basis": None,
                    "source": None,
                    "exception": None,
                    "exception_type": None,
                    "experiment": experiment.slug,
                    "filename": "experimenter/jetstream/client.py",
                    "func_name": "load_data_from_gcs",
                    "log_level": "WARNING",
                    "message": f"Could not find data in analysis bucket at path metadata/metadata_{experiment.slug.replace('-', '_')}.json",  # noqa: E501
                    "metric": None,
                    "segment": None,
                    "statistic": None,
                    "timestamp": now.isoformat(timespec="milliseconds").removesuffix(
                        "+00:00"
                    )
                    + "Z",
                },
                {
                    "analysis_basis": None,
                    "source": None,
                    "exception": None,
                    "exception_type": None,
                    "experiment": experiment.slug,
                    "filename": "experimenter/jetstream/client.py",
                    "func_name": "load_data_from_gcs",
                    "log_level": "WARNING",
                    "message": f"Could not find data in analysis bucket at path errors/errors_{experiment.slug.replace('-', '_')}.json",  # noqa: E501
                    "metric": None,
                    "segment": None,
                    "statistic": None,
                    "timestamp": now.isoformat(timespec="milliseconds").removesuffix(
                        "+00:00"
                    )
                    + "Z",
                },
                {
                    "analysis_basis": None,
                    "source": None,
                    "exception": None,
                    "exception_type": None,
                    "experiment": experiment.slug,
                    "filename": "experimenter/jetstream/client.py",
                    "func_name": "load_data_from_gcs",
                    "log_level": "WARNING",
                    "message": f"Could not find data in analysis bucket at path statistics/statistics_{experiment.slug.replace('-', '_')}_daily.json",  # noqa: E501
                    "metric": None,
                    "segment": None,
                    "statistic": None,
                    "timestamp": now.isoformat(timespec="milliseconds").removesuffix(
                        "+00:00"
                    )
                    + "Z",
                },
            ]
            if experiment.results_ready:
                experiment_errors.append(
                    {
                        "analysis_basis": None,
                        "source": None,
                        "exception": None,
                        "exception_type": None,
                        "experiment": experiment.slug,
                        "filename": "experimenter/jetstream/client.py",
                        "func_name": "load_data_from_gcs",
                        "log_level": "WARNING",
                        "message": f"Could not find data in analysis bucket at path statistics/statistics_{experiment.slug.replace('-', '_')}_weekly.json",  # noqa: E501
                        "metric": None,
                        "segment": None,
                        "statistic": None,
                        "timestamp": now.isoformat(timespec="milliseconds").removesuffix(
                            "+00:00"
                        )
                        + "Z",
                    }
                )

            if (
                lifecycle == NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
                and offset > 1
            ):
                experiment_errors.append(
                    {
                        "analysis_basis": None,
                        "source": None,
                        "exception": None,
                        "exception_type": None,
                        "experiment": experiment.slug,
                        "filename": "experimenter/jetstream/client.py",
                        "func_name": "load_data_from_gcs",
                        "log_level": "WARNING",
                        "message": f"Could not find data in analysis bucket at path statistics/statistics_{experiment.slug.replace('-', '_')}_overall.json",  # noqa: E501
                        "metric": None,
                        "segment": None,
                        "statistic": None,
                        "timestamp": now.isoformat(timespec="milliseconds").removesuffix(
                            "+00:00"
                        )
                        + "Z",
                    },
                )

            tasks.fetch_experiment_data(experiment.id)
            experiment = NimbusExperiment.objects.get(id=experiment.id)
            self.assertEqual(
                experiment.results_data,
                {
                    "v3": {
                        "metadata": None,
                        "overall": {},
                        "daily": {},
                        "weekly": {},
                        "errors": {
                            "experiment": experiment_errors,
                        },
                    },
                },
            )
            self.assertFalse(experiment.has_displayable_results)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_invalid_exposure_data_does_not_override_other_metrics(self, lifecycle):
        primary_outcomes = ["default-browser"]
        secondary_outcomes = ["secondary_outcome"]
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=primary_outcomes,
            secondary_outcomes=secondary_outcomes,
        )

        (
            DAILY_DATA,
            _,
            _,
            _,
            _,
            SEGMENT_DATA,
            _,
            _,
        ) = JetstreamTestData.get_test_data(primary_outcomes)

        OTHER_METRICS = {
            Group.OTHER.value: {
                "some_count": "Some Count",
                "another_count": "Another Count",
                "some_dau_impact": "Some Dau Impact",
                "some_ratio": "Some Ratio",
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
                    + [
                        # This list of exposure points is intentionally incomplete as we
                        # want to test that other_metrics is not overridden even if some
                        # expected data is missing
                        {
                            "metric": "identity",
                            "statistic": "count",
                            "branch": "control",
                            "point": 10,
                            "segment": "all",
                            "analysis_basis": "exposures",
                            "window_index": "1",
                        }
                    ]
                )

        def open_file(filename):
            return File(filename)

        with (
            patch("experimenter.jetstream.client.analysis_storage.open") as mock_open,
            patch("experimenter.jetstream.client.analysis_storage.exists") as mock_exists,
        ):
            mock_open.side_effect = open_file
            mock_exists.return_value = True

            tasks.fetch_experiment_data(experiment.id)
            experiment = NimbusExperiment.objects.get(id=experiment.id)
            self.assertEqual(
                experiment.results_data.get("v3", {}).get("other_metrics"), OTHER_METRICS
            )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.has_missing_expected_results")
    @patch("experimenter.jetstream.tasks.get_stored_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_latest_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_results_filenames")
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_fetch_jetstream_data_fetches_when_analysis_start_time_is_newer(
        self,
        lifecycle,
        mock_delay,
        mock_get_results_filenames,
        mock_get_latest_analysis_start_time,
        mock_get_stored_analysis_start_time,
        mock_has_missing_expected_results,
    ):
        latest_time = timezone.now()

        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)

        mock_get_latest_analysis_start_time.return_value = latest_time
        mock_get_stored_analysis_start_time.return_value = (
            latest_time - datetime.timedelta(days=1)
        )
        mock_has_missing_expected_results.return_value = False
        tasks.fetch_jetstream_data()

        mock_get_latest_analysis_start_time.assert_called_once_with(experiment.slug)
        mock_delay.assert_called_once_with(experiment.id)

    @patch("experimenter.jetstream.tasks.has_missing_expected_results")
    @patch("experimenter.jetstream.tasks.get_stored_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_latest_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_results_filenames")
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_fetch_jetstream_data_skips_when_analysis_start_time_is_not_newer(
        self,
        mock_delay,
        mock_get_results_filenames,
        mock_get_latest_analysis_start_time,
        mock_get_stored_analysis_start_time,
        mock_has_missing_expected_results,
    ):
        current_time = timezone.now()

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )

        mock_get_latest_analysis_start_time.return_value = current_time
        mock_get_stored_analysis_start_time.return_value = current_time
        mock_has_missing_expected_results.return_value = False
        tasks.fetch_jetstream_data()

        mock_get_latest_analysis_start_time.assert_called_once_with(experiment.slug)
        mock_delay.assert_not_called()

    @patch("experimenter.jetstream.tasks.has_missing_expected_results")
    @patch("experimenter.jetstream.tasks.get_stored_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_latest_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_results_filenames")
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_fetch_jetstream_data_fetches_when_stored_analysis_start_time_is_missing(
        self,
        mock_delay,
        mock_get_results_filenames,
        mock_get_latest_analysis_start_time,
        mock_get_stored_analysis_start_time,
        mock_has_missing_expected_results,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            results_data=None,
        )

        mock_get_latest_analysis_start_time.return_value = timezone.now()
        mock_get_stored_analysis_start_time.return_value = None
        mock_has_missing_expected_results.return_value = False
        tasks.fetch_jetstream_data()

        mock_get_latest_analysis_start_time.assert_called_once_with(experiment.slug)
        mock_delay.assert_called_once_with(experiment.id)

    @patch("experimenter.jetstream.tasks.has_missing_expected_results")
    @patch("experimenter.jetstream.tasks.get_stored_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_latest_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_results_filenames")
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_fetch_jetstream_data_skips_when_no_analysis_start_time_exists(
        self,
        mock_delay,
        mock_get_results_filenames,
        mock_get_latest_analysis_start_time,
        mock_get_stored_analysis_start_time,
        mock_has_missing_expected_results,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )

        mock_get_latest_analysis_start_time.return_value = None
        mock_has_missing_expected_results.return_value = False
        tasks.fetch_jetstream_data()

        mock_get_latest_analysis_start_time.assert_called_once_with(experiment.slug)
        mock_delay.assert_not_called()

    @patch("experimenter.jetstream.tasks.has_missing_expected_results")
    @patch("experimenter.jetstream.tasks.get_stored_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_latest_analysis_start_time")
    @patch("experimenter.jetstream.tasks.get_results_filenames")
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_fetch_jetstream_data_fetches_when_expecting_missing_results(
        self,
        mock_delay,
        mock_get_results_filenames,
        mock_get_latest_analysis_start_time,
        mock_get_stored_analysis_start_time,
        mock_has_missing_expected_results,
    ):
        current_time = timezone.now()

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )

        mock_get_latest_analysis_start_time.return_value = current_time
        mock_get_stored_analysis_start_time.return_value = current_time
        mock_has_missing_expected_results.return_value = True
        tasks.fetch_jetstream_data()

        mock_has_missing_expected_results.assert_called_once()
        mock_delay.assert_called_once_with(experiment.id)

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

    @patch("experimenter.jetstream.client.analysis_storage.open")
    @patch("experimenter.jetstream.client.analysis_storage.exists")
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

        sizing_results = cache.get(settings.SIZING_DATA_KEY)
        self.assertIsNone(sizing_results)

        tasks.fetch_population_sizing_data()
        sizing_results = SampleSizes.parse_raw(cache.get(settings.SIZING_DATA_KEY))

        self.assertEqual(
            json.loads(sizing_test_data),
            sizing_results.model_dump(exclude_unset=True),
        )

    @patch("experimenter.jetstream.client.analysis_storage.open")
    @patch("experimenter.jetstream.client.analysis_storage.exists")
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

        sizing_results = cache.get(settings.SIZING_DATA_KEY)
        self.assertIsNone(sizing_results)

        tasks.fetch_population_sizing_data()
        sizing_results = cache.get(settings.SIZING_DATA_KEY)
        self.assertEqual(sizing_results, "{}")

    @patch("experimenter.jetstream.client.analysis_storage.open")
    @patch("experimenter.jetstream.client.analysis_storage.exists")
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

    def test_get_stored_analysis_start_time_returns_parsed_time(self):
        analysis_start_time = "2022-08-31T04:30:03+00:00"
        experiment = NimbusExperimentFactory.create(
            results_data={
                "v3": {"metadata": {"analysis_start_time": analysis_start_time}}
            },
        )

        self.assertEqual(
            get_stored_analysis_start_time(experiment),
            datetime.datetime.fromisoformat(analysis_start_time),
        )

    def test_get_stored_analysis_start_time_none_when_no_results_data(self):
        experiment = NimbusExperimentFactory.create(results_data=None)

        self.assertIsNone(get_stored_analysis_start_time(experiment))

    def test_get_stored_analysis_start_time_none_when_no_metadata(self):
        experiment = NimbusExperimentFactory.create(results_data={"v3": {}})

        self.assertIsNone(get_stored_analysis_start_time(experiment))

    @patch("experimenter.jetstream.client.get_metadata")
    def test_get_latest_analysis_start_time_returns_parsed_time(self, mock_get_metadata):
        analysis_start_time = "2022-08-31T04:30:03+00:00"
        mock_get_metadata.return_value = {"analysis_start_time": analysis_start_time}

        self.assertEqual(
            get_latest_analysis_start_time("test-experiment-slug"),
            datetime.datetime.fromisoformat(analysis_start_time),
        )

    @patch("experimenter.jetstream.client.get_metadata")
    def test_get_latest_analysis_start_time_none_when_metadata_missing(
        self, mock_get_metadata
    ):
        mock_get_metadata.side_effect = RuntimeError

        self.assertIsNone(get_latest_analysis_start_time("test-experiment-slug"))

    @patch("experimenter.jetstream.client.analysis_storage.listdir")
    def test_get_results_filenames_returns_filenames_by_folder(self, mock_listdir):
        def listdir(folder):
            return ([], [f"{folder}_a.json", f"{folder}_b.json"])

        mock_listdir.side_effect = listdir

        self.assertEqual(
            get_results_filenames(),
            {
                STATISTICS_FOLDER: {"statistics_a.json", "statistics_b.json"},
                METADATA_FOLDER: {"metadata_a.json", "metadata_b.json"},
                ERRORS_FOLDER: {"errors_a.json", "errors_b.json"},
            },
        )

    def test_expected_windows_daily_only(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            start_date=datetime.date.today(),
            proposed_enrollment=30,
        )

        self.assertFalse(experiment.results_ready)
        self.assertIsNone(experiment.end_date)
        self.assertEqual(expected_windows(experiment), [AnalysisWindow.DAILY])

    def test_expected_windows_includes_weekly_when_results_ready(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            start_date=datetime.date(2020, 1, 1),
            proposed_enrollment=12,
        )

        self.assertTrue(experiment.results_ready)
        self.assertIsNone(experiment.end_date)
        self.assertEqual(
            expected_windows(experiment),
            [AnalysisWindow.DAILY, AnalysisWindow.WEEKLY],
        )

    def test_expected_windows_includes_overall_after_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )
        experiment._enrollment_end_date = datetime.date(2019, 5, 15)
        experiment._end_date = datetime.date(2019, 8, 1)
        experiment.save()

        self.assertTrue(experiment.results_ready)
        self.assertEqual(
            expected_windows(experiment),
            [AnalysisWindow.DAILY, AnalysisWindow.WEEKLY, AnalysisWindow.OVERALL],
        )

    def test_has_missing_expected_results_true_when_expected_file_absent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            start_date=datetime.date.today(),
            proposed_enrollment=30,
        )
        results_filenames = {STATISTICS_FOLDER: set()}

        self.assertTrue(has_missing_expected_results(experiment, results_filenames))

    def test_has_missing_expected_results_false_when_expected_file_present(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            start_date=datetime.date.today(),
            proposed_enrollment=30,
        )
        recipe_slug = experiment.slug.replace("-", "_")
        results_filenames = {STATISTICS_FOLDER: {f"statistics_{recipe_slug}_daily.json"}}

        self.assertFalse(has_missing_expected_results(experiment, results_filenames))

    def test_has_missing_expected_results_false_past_analysis_buffer(self):
        offset = NimbusExperiment.DAYS_ANALYSIS_BUFFER + 10
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date(2020, 1, 1),
            proposed_enrollment=12,
            end_date=datetime.date.today() - datetime.timedelta(days=offset),
        )
        results_filenames = {STATISTICS_FOLDER: set()}

        self.assertFalse(has_missing_expected_results(experiment, results_filenames))

    @patch("experimenter.jetstream.tasks.generate_nimbus_changelog")
    @patch("experimenter.jetstream.tasks.get_experiment_data")
    def test_fetch_experiment_data_saves_when_results_changed(
        self, mock_get_experiment_data, mock_generate_nimbus_changelog
    ):
        experiment = NimbusExperimentFactory.create(
            results_data={"v3": {"metadata": {"analysis_start_time": "old"}}},
        )
        new_results_data = {"v3": {"metadata": {"analysis_start_time": "new"}}}

        mock_get_experiment_data.return_value = new_results_data
        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(experiment.results_data, new_results_data)

    @patch("experimenter.jetstream.tasks.get_experiment_data")
    def test_fetch_experiment_data_does_not_save_when_results_unchanged(
        self, mock_get_experiment_data
    ):
        experiment = NimbusExperimentFactory.create(
            results_data={"v3": {"metadata": {}}},
        )

        mock_get_experiment_data.return_value = experiment.results_data

        with patch.object(NimbusExperiment, "save") as mock_save:
            tasks.fetch_experiment_data(experiment.id)

        mock_save.assert_not_called()

    @patch("experimenter.jetstream.tasks.get_results_filenames")
    @patch("experimenter.jetstream.tasks.get_latest_analysis_start_time")
    def test_fetch_jetstream_data_raises_exception(
        self, mock_get_latest_analysis_start_time, mock_get_results_filenames
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )

        mock_get_latest_analysis_start_time.side_effect = Exception

        with self.assertRaises(Exception):
            tasks.fetch_jetstream_data()

        mock_get_latest_analysis_start_time.assert_called_once_with(experiment.slug)


@pytest.fixture
def mock_monitoring_data(request):
    data = {
        "total_enrollments": 15000,
        "total_unenrollments": 1200,
        "branches": {
            "control": {
                "enrollments": 7500,
                "unenrollments": 580,
            },
            "treatment-a": {
                "enrollments": 7500,
                "unenrollments": 620,
            },
        },
        "unenrollment_reasons": {},
        "reasons_by_branch": {
            "control": {
                "targeting-mismatch": {"1pct_count": 85},
                "studies-opt-out": {"1pct_count": 42},
                "unknown": {"1pct_count": 15},
            },
            "treatment-a": {
                "studies-opt-out": {"1pct_count": 98},
                "targeting-mismatch": {"1pct_count": 72},
                "user-request": {"1pct_count": 28},
            },
        },
    }
    if request.instance:
        request.instance.monitoring_data = data
    return data


@pytest.fixture
def mock_funnel_entries(request):
    data = [
        {
            "app_name": APPLICATION_CONFIG_DESKTOP.app_name,
            "branch": "control",
            "status": NimbusExperiment.FunnelStatus.ENROLLED,
            "reason": NimbusExperiment.FunnelReason.QUALIFIED,
            "conflict_slug": None,
            "client_count": 11100,
        },
        {
            "app_name": APPLICATION_CONFIG_DESKTOP.app_name,
            "branch": None,
            "status": NimbusExperiment.FunnelStatus.NOT_ENROLLED,
            "reason": NimbusExperiment.FunnelReason.NOT_TARGETED,
            "conflict_slug": None,
            "client_count": 67677700,
        },
        {
            "app_name": APPLICATION_CONFIG_DESKTOP.app_name,
            "branch": None,
            "status": NimbusExperiment.FunnelStatus.NOT_ENROLLED,
            "reason": NimbusExperiment.FunnelReason.OPT_OUT,
            "conflict_slug": None,
            "client_count": 2009500,
        },
        {
            "app_name": APPLICATION_CONFIG_DESKTOP.app_name,
            "branch": None,
            "status": NimbusExperiment.FunnelStatus.NOT_ENROLLED,
            "reason": NimbusExperiment.FunnelReason.NOT_SELECTED,
            "conflict_slug": None,
            "client_count": 6205100,
        },
        {
            "app_name": APPLICATION_CONFIG_DESKTOP.app_name,
            "branch": None,
            "status": NimbusExperiment.FunnelStatus.NOT_ENROLLED,
            "reason": NimbusExperiment.FunnelReason.FEATURE_CONFLICT,
            "conflict_slug": "us-billboard-rollout-2026",
            "client_count": 49800,
        },
    ]
    if request.instance:
        request.instance.funnel_entries = data
    return data


@pytest.mark.usefixtures("mock_monitoring_data", "mock_funnel_entries")
class TestFetchMonitoringDataTask(TestCase):
    def setUp(self):
        super().setUp()
        patcher = patch("experimenter.jetstream.tasks.get_monitoring_data")
        self.mock_get_monitoring_data = patcher.start()
        self.addCleanup(patcher.stop)

        self._funnel_patcher = patch(
            "experimenter.jetstream.tasks.get_enrollment_funnel_data"
        )
        self.mock_get_funnel_data = self._funnel_patcher.start()
        self.mock_get_funnel_data.return_value = {"v1": {}}

    def tearDown(self):
        self._funnel_patcher.stop()

    @parameterized.expand([(None,), ({},)])
    def test_fetch_monitoring_data_no_data(self, return_value):
        self.mock_get_monitoring_data.return_value = return_value

        tasks.fetch_monitoring_data()

        self.mock_get_monitoring_data.assert_called_once()

    def test_fetch_monitoring_data_updates_live_experiment(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data={},
        )
        self.mock_get_monitoring_data.return_value = {
            "v1": {experiment.slug: self.monitoring_data}
        }

        tasks.fetch_monitoring_data()

        experiment.refresh_from_db()
        self.assertEqual(
            experiment.monitoring_data,
            {**self.monitoring_data, "enrollment_funnel": []},
        )
        self.assertIsNotNone(experiment.monitoring_data_updated_at)

    def test_fetch_monitoring_data_merges_funnel_data(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data={},
        )
        self.mock_get_monitoring_data.return_value = {
            "v1": {experiment.slug: self.monitoring_data}
        }
        self.mock_get_funnel_data.return_value = {
            "v1": {experiment.slug: self.funnel_entries}
        }

        tasks.fetch_monitoring_data()

        experiment.refresh_from_db()
        self.assertEqual(
            experiment.monitoring_data,
            {**self.monitoring_data, "enrollment_funnel": self.funnel_entries},
        )

    def test_fetch_monitoring_data_funnel_defaults_to_empty_list_when_missing(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data={},
        )
        self.mock_get_monitoring_data.return_value = {
            "v1": {experiment.slug: self.monitoring_data}
        }
        self.mock_get_funnel_data.return_value = {"v1": {}}

        tasks.fetch_monitoring_data()

        experiment.refresh_from_db()
        self.assertEqual(experiment.monitoring_data["enrollment_funnel"], [])

    def test_fetch_monitoring_data_continues_if_funnel_fetch_fails(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data={},
        )
        self.mock_get_monitoring_data.return_value = {
            "v1": {experiment.slug: self.monitoring_data}
        }
        self.mock_get_funnel_data.side_effect = Exception("GCS unavailable")

        tasks.fetch_monitoring_data()

        experiment.refresh_from_db()
        self.assertEqual(experiment.monitoring_data["enrollment_funnel"], [])

    @parameterized.expand(
        [
            (NimbusExperiment.Status.DRAFT,),
            (NimbusExperiment.Status.PREVIEW,),
            (NimbusExperiment.Status.COMPLETE,),
        ]
    )
    def test_fetch_monitoring_data_skips_non_live_experiment(self, status):
        experiment = NimbusExperimentFactory.create(
            status=status,
            monitoring_data={},
        )
        self.mock_get_monitoring_data.return_value = {
            "v1": {experiment.slug: self.monitoring_data}
        }

        tasks.fetch_monitoring_data()

        experiment.refresh_from_db()
        self.assertEqual(experiment.monitoring_data, {})
        self.assertIsNone(experiment.monitoring_data_updated_at)

    def test_fetch_monitoring_data_skips_nonexistent_experiment(self):
        self.mock_get_monitoring_data.return_value = {
            "v1": {"nonexistent-slug": self.monitoring_data}
        }

        tasks.fetch_monitoring_data()

        self.mock_get_monitoring_data.assert_called_once()

    def test_fetch_monitoring_data_no_update_if_data_unchanged(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data=self.monitoring_data,
        )
        self.mock_get_monitoring_data.return_value = {
            "v1": {experiment.slug: self.monitoring_data}
        }

        with patch.object(experiment, "save") as mock_save:
            tasks.fetch_monitoring_data()
            mock_save.assert_not_called()

    def test_fetch_monitoring_data_handles_update_exception(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data={},
        )
        self.mock_get_monitoring_data.return_value = {
            "v1": {experiment.slug: self.monitoring_data}
        }

        with (
            patch.object(experiment, "save", side_effect=Exception("DB error")),
            patch(
                "experimenter.jetstream.tasks.NimbusExperiment.objects.get"
            ) as mock_get,
            patch("experimenter.jetstream.tasks.logger") as mock_logger,
        ):
            mock_get.return_value = experiment
            tasks.fetch_monitoring_data()
            mock_logger.error.assert_called_once()

    def test_fetch_monitoring_data_updates_multiple_experiments(self):
        exp1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data={},
        )
        exp2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            monitoring_data={},
        )
        data1 = dict(self.monitoring_data, total_enrollments=15000)
        data2 = dict(self.monitoring_data, total_enrollments=25000)
        self.mock_get_monitoring_data.return_value = {
            "v1": {
                exp1.slug: data1,
                exp2.slug: data2,
            }
        }

        tasks.fetch_monitoring_data()

        exp1.refresh_from_db()
        exp2.refresh_from_db()
        self.assertEqual(exp1.monitoring_data, {**data1, "enrollment_funnel": []})
        self.assertEqual(exp2.monitoring_data, {**data2, "enrollment_funnel": []})

    def test_fetch_monitoring_data_fatal_error(self):
        self.mock_get_monitoring_data.side_effect = Exception("GCS connection failed")

        with self.assertRaises(Exception) as context:
            tasks.fetch_monitoring_data()

        self.assertIn("GCS connection failed", str(context.exception))


class TestGetMonitoringData(TestCase):
    @patch("experimenter.jetstream.client.load_data_from_gcs")
    def test_get_monitoring_data_success(self, mock_load):
        data = {
            "v1": {
                "experiment-1": {
                    "total_enrollments": 15000,
                    "branches": {"control": {"enrollments": 7500}},
                }
            }
        }
        mock_load.return_value = data

        result = get_monitoring_data()

        self.assertEqual(result, data)
        mock_load.assert_called_once_with(
            "enrollment_counts/enrollment_counts_latest.json"
        )

    @patch("experimenter.jetstream.client.load_data_from_gcs")
    def test_get_monitoring_data_no_data(self, mock_load):
        mock_load.return_value = None

        result = get_monitoring_data()

        self.assertIsNone(result)

    @patch("experimenter.jetstream.client.load_data_from_gcs")
    def test_get_monitoring_data_exception(self, mock_load):
        mock_load.side_effect = RuntimeError("GCS error")

        with self.assertRaises(RuntimeError):
            get_monitoring_data()


@pytest.mark.usefixtures("mock_funnel_entries")
class TestGetEnrollmentFunnelData(TestCase):
    @patch("experimenter.jetstream.client.load_data_from_gcs")
    def test_get_enrollment_funnel_data_success(self, mock_load):
        data = {"v1": {"experiment-1": self.funnel_entries}}
        mock_load.return_value = data

        result = get_enrollment_funnel_data()

        self.assertEqual(result, data)
        mock_load.assert_called_once_with(
            "enrollment_counts/enrollment_funnel_v1_latest.json"
        )

    @patch("experimenter.jetstream.client.load_data_from_gcs")
    def test_get_enrollment_funnel_data_no_data(self, mock_load):
        mock_load.return_value = None

        result = get_enrollment_funnel_data()

        self.assertIsNone(result)

    @patch("experimenter.jetstream.client.load_data_from_gcs")
    def test_get_enrollment_funnel_data_exception(self, mock_load):
        mock_load.side_effect = RuntimeError("GCS error")

        with self.assertRaises(RuntimeError):
            get_enrollment_funnel_data()


class TestGetFeatmonSlugs(TestCase):
    def setUp(self):
        super().setUp()
        get_featmon_slugs.cache_clear()

    def tearDown(self):
        super().tearDown()
        get_featmon_slugs.cache_clear()

    def test_returns_slugs_from_slug_field(self):
        toml = '[features.my_feature]\nslug = "my-feature"\n'
        with patch("pathlib.Path.read_text", return_value=toml):
            self.assertIn("my-feature", get_featmon_slugs())

    def test_derives_slug_from_key_when_no_slug_field(self):
        toml = "[features.my_feature]\n"
        with patch("pathlib.Path.read_text", return_value=toml):
            self.assertIn("my-feature", get_featmon_slugs())

    def test_returns_empty_frozenset_when_file_not_found(self):
        with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
            self.assertEqual(get_featmon_slugs(), frozenset())

    def test_returns_empty_frozenset_when_toml_invalid(self):
        import tomllib

        with patch("pathlib.Path.read_text", side_effect=tomllib.TOMLDecodeError):
            self.assertEqual(get_featmon_slugs(), frozenset())

    def test_returns_multiple_slugs(self):
        toml = (
            '[features.feature_a]\nslug = "feature-a"\n'
            '[features.feature_b]\nslug = "feature-b"\n'
        )
        with patch("pathlib.Path.read_text", return_value=toml):
            slugs = get_featmon_slugs()
            self.assertIn("feature-a", slugs)
            self.assertIn("feature-b", slugs)

    def test_result_is_cached(self):
        toml = '[features.my_feature]\nslug = "my-feature"\n'
        with patch("pathlib.Path.read_text", return_value=toml) as mock_read:
            get_featmon_slugs()
            get_featmon_slugs()
            mock_read.assert_called_once()


class TestUpdateHoldbackEnrollmentPeriod(TestCase):
    def test_sets_do_rerun_on_first_trigger(self):
        today = datetime.date.today()
        # 28 days ago: first trigger — sets both do_rerun and do_rerun_timestamp
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_holdback=True,
            _start_date=today - datetime.timedelta(days=28),
            proposed_enrollment=14,
            proposed_duration=84,
        )
        tasks.update_holdback_enrollment_period()
        experiment.refresh_from_db()

        self.assertTrue(experiment.do_rerun)
        self.assertIsNotNone(experiment.do_rerun_timestamp)

    def test_updates_only_timestamp_on_subsequent_triggers(self):
        today = datetime.date.today()
        # 35 days: do_rerun already True — only do_rerun_timestamp should update
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_holdback=True,
            _start_date=today - datetime.timedelta(days=35),
            proposed_enrollment=14,
            proposed_duration=84,
            do_rerun=True,
        )
        tasks.update_holdback_enrollment_period()
        experiment.refresh_from_db()

        self.assertTrue(experiment.do_rerun)
        self.assertIsNotNone(experiment.do_rerun_timestamp)

    def test_skips_holdback_with_enrollment_stopped(self):
        today = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_holdback=True,
            _start_date=today - datetime.timedelta(days=35),
            _enrollment_end_date=today - datetime.timedelta(days=7),
            proposed_enrollment=14,
            proposed_duration=84,
        )
        tasks.update_holdback_enrollment_period()
        experiment.refresh_from_db()

        self.assertFalse(experiment.do_rerun)

    def test_skips_experiment_below_minimum_days(self):
        today = datetime.date.today()
        # Started 20 days ago: 20 < 28 (minimum), so should be skipped
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_holdback=True,
            _start_date=today - datetime.timedelta(days=20),
            proposed_enrollment=14,
            proposed_duration=84,
        )
        tasks.update_holdback_enrollment_period()
        experiment.refresh_from_db()

        self.assertFalse(experiment.do_rerun)

    def test_skips_experiment_not_on_weekly_boundary(self):
        today = datetime.date.today()
        # Started 29 days ago: >= 28 but 29 % 7 != 0, so should be skipped
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_holdback=True,
            _start_date=today - datetime.timedelta(days=29),
            proposed_enrollment=14,
            proposed_duration=84,
        )
        tasks.update_holdback_enrollment_period()
        experiment.refresh_from_db()

        self.assertFalse(experiment.do_rerun)

    def test_skips_ended_holdback(self):
        today = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_holdback=True,
            _start_date=today - datetime.timedelta(days=50),
            proposed_enrollment=14,
            proposed_duration=84,
        )
        experiment._end_date = today - datetime.timedelta(days=1)
        experiment.save(update_fields=["_end_date"])
        tasks.update_holdback_enrollment_period()
        experiment.refresh_from_db()

        self.assertFalse(experiment.do_rerun)

    def test_skips_non_holdback_experiments(self):
        today = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_holdback=False,
            _start_date=today - datetime.timedelta(days=50),
            proposed_enrollment=14,
            proposed_duration=84,
        )
        tasks.update_holdback_enrollment_period()
        experiment.refresh_from_db()

        self.assertFalse(experiment.do_rerun)

    def test_raises_on_unexpected_error(self):
        with (
            patch(
                "experimenter.jetstream.tasks.NimbusExperiment.objects.filter",
                side_effect=Exception("db error"),
            ),
            self.assertRaises(Exception, msg="db error"),
        ):
            tasks.update_holdback_enrollment_period()
