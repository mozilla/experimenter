import datetime
import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from parameterized import parameterized

from experimenter.experiments.constants import NimbusConstants
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
            ERRORS,
            SEGMENT_DATA,
            DAILY_EXPOSURES_DATA,
            SEGMENT_EXPOSURES_DATA,
        ) = JetstreamTestData.get_test_data(primary_outcomes)

        FULL_DATA = {
            "v2": {
                "daily": {
                    "enrollments": {
                        "all": DAILY_DATA,
                        "some_segment": SEGMENT_DATA,
                    },
                    "exposures": {
                        "all": DAILY_EXPOSURES_DATA,
                        "some_segment": SEGMENT_EXPOSURES_DATA,
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
                                            "difference": {"all": [], "first": {}},
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "percent": 50.0,
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "percent": 50.0,
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "percent": 50.0,
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "percent": 50.0,
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                    "default_browser_null"
                                ],
                                "default_metrics": []
                            }
                        }
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
                "daily": {
                    "enrollments": {
                        "all": DAILY_DATA,
                        "some_segment": SEGMENT_DATA,
                    },
                    "exposures": {
                        "all": DAILY_EXPOSURES_DATA,
                        "some_segment": SEGMENT_EXPOSURES_DATA,
                    },
                },
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
                "daily": {
                    "enrollments": {
                        "all": DAILY_DATA,
                        "some_segment": SEGMENT_DATA,
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
                                            "difference": {"all": [], "first": {}},
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "percent": 0.0,
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                                            "difference": {"all": [], "first": {}},
                                            "percent": 0.0,
                                            "relative_uplift": {"all": [], "first": {}},
                                            "significance": {"overall": {}, "weekly": {}},
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
                    Group.OTHER: {
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
            (NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_live(self, lifecycle, mock_delay):
        # continue to fetch data while LIVE, even after proposed end date
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, start_date=datetime.date(2020, 1, 1), proposed_enrollment=12
        )
        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_skip_old_complete(self, lifecycle, mock_delay):
        # don't fetch COMPLETE experiment after proposed end date + buffer
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, start_date=datetime.date(2020, 1, 1), proposed_enrollment=12
        )
        experiment.results_data = {}
        experiment.save()

        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_skip_preview(self, lifecycle, mock_delay):
        # don't fetch PREVIEW experiments
        offset = NimbusConstants.DAYS_ANALYSIS_BUFFER + 1
        _ = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=offset)
        )
        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_expired_in_loop(self, lifecycle, mock_delay):
        offset = NimbusConstants.DAYS_ANALYSIS_BUFFER + 1
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

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_null_fetches(self, lifecycle, mock_delay):
        offset = NimbusConstants.DAYS_ANALYSIS_BUFFER + 1
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, end_date=datetime.date.today() - datetime.timedelta(days=offset)
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
