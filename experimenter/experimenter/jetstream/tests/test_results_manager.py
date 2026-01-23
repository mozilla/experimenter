from django.test import TestCase
from parameterized.parameterized import parameterized

from experimenter.experiments.models import (
    NimbusExperiment,
)
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusExperimentFactory,
)
from experimenter.jetstream.results_manager import ExperimentResultsManager
from experimenter.metrics import MetricAreas
from experimenter.metrics.tests import mock_valid_metrics
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes


@mock_valid_outcomes
class TestExperimentResultsManager(TestCase):
    def setUp(self):
        application = NimbusExperiment.Application.DESKTOP
        Outcomes.clear_cache()
        self.desktop_outcome_1 = Outcomes.get_by_slug_and_application(
            "desktop_outcome_1", application
        )
        self.experiment = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[self.desktop_outcome_1.slug],
            secondary_outcomes=[],
        )
        NimbusBranchFactory.create(
            experiment=self.experiment, name="Branch A", slug="branch-a"
        )
        NimbusBranchFactory.create(
            experiment=self.experiment, name="Branch B", slug="branch-b"
        )
        self.results_manager = ExperimentResultsManager(self.experiment)

    def test_get_weekly_metric_data(self):
        self.experiment.results_data = {
            "v3": {
                "weekly": {
                    "enrollments": {
                        "all": {
                            "branch-a": {
                                "branch_data": {
                                    "other_metrics": {
                                        "urlbar_amazon_search_count": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 140,
                                                        "upper": 160,
                                                        "point": 150,
                                                    },
                                                    {
                                                        "lower": 130,
                                                        "upper": 150,
                                                        "point": 140,
                                                    },
                                                    {
                                                        "lower": 120,
                                                        "upper": 140,
                                                        "point": 130,
                                                    },
                                                ]
                                            },
                                            "relative_uplift": {
                                                "branch-a": {"all": []},
                                            },
                                        }
                                    }
                                },
                            },
                            "branch-b": {
                                "branch_data": {
                                    "other_metrics": {
                                        "urlbar_amazon_search_count": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 140,
                                                        "upper": 160,
                                                        "point": 150,
                                                    },
                                                    {
                                                        "lower": 130,
                                                        "upper": 150,
                                                        "point": 140,
                                                    },
                                                    {
                                                        "lower": 120,
                                                        "upper": 140,
                                                        "point": 130,
                                                    },
                                                ]
                                            },
                                            "relative_uplift": {
                                                "branch-a": {
                                                    "all": [
                                                        {
                                                            "lower": 10,
                                                            "upper": 20,
                                                            "point": 15,
                                                        },
                                                        {
                                                            "lower": 5,
                                                            "upper": 15,
                                                            "point": 10,
                                                        },
                                                        {
                                                            "lower": 0,
                                                            "upper": 10,
                                                            "point": 5,
                                                        },
                                                    ]
                                                },
                                                "branch-b": {"all": []},
                                            },
                                        }
                                    }
                                }
                            },
                        }
                    }
                }
            }
        }
        self.experiment.save()

        expected_weekly_data = {
            "urlbar_amazon_search_count": {
                "data": {
                    "branch-a": [
                        (
                            {"lower": 140, "upper": 160, "significance": "neutral"},
                            None,
                        ),
                        (
                            {"lower": 130, "upper": 150, "significance": "neutral"},
                            None,
                        ),
                        (
                            {"lower": 120, "upper": 140, "significance": "neutral"},
                            None,
                        ),
                    ],
                    "branch-b": [
                        (
                            {"lower": 140, "upper": 160, "significance": "neutral"},
                            {
                                "avg_rel_change": 15,
                                "lower": 10,
                                "upper": 20,
                                "significance": "neutral",
                            },
                        ),
                        (
                            {"lower": 130, "upper": 150, "significance": "neutral"},
                            {
                                "avg_rel_change": 10,
                                "lower": 5,
                                "upper": 15,
                                "significance": "neutral",
                            },
                        ),
                        (
                            {"lower": 120, "upper": 140, "significance": "neutral"},
                            {
                                "avg_rel_change": 5,
                                "lower": 0,
                                "upper": 10,
                                "significance": "neutral",
                            },
                        ),
                    ],
                },
                "has_weekly_data": True,
            },
            "total_amazon_search_count": {
                "data": {},
                "has_weekly_data": False,
            },
            "retained": {
                "data": {},
                "has_weekly_data": False,
            },
            "client_level_daily_active_users_v2": {
                "data": {},
                "has_weekly_data": False,
            },
            "search_count": {
                "data": {},
                "has_weekly_data": False,
            },
        }

        self.assertEqual(
            self.results_manager.get_weekly_metric_data("enrollments", "all", "branch-a"),
            expected_weekly_data,
        )

    def test_get_metric_data_returns_correct_data(self):
        self.experiment.results_data = {
            "v3": {
                "overall": {
                    "enrollments": {
                        "all": {
                            "branch-a": {
                                "branch_data": {
                                    "other_metrics": {
                                        "urlbar_amazon_search_count": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 1.49,
                                                        "upper": 1.74,
                                                        "point": 1.62,
                                                    }
                                                ]
                                            },
                                            "relative_uplift": {
                                                "branch-a": {"all": []},
                                                "branch-b": {
                                                    "all": [
                                                        {
                                                            "lower": -0.12,
                                                            "upper": 0.15,
                                                            "point": 0.02,
                                                        }
                                                    ]
                                                },
                                            },
                                            "significance": {
                                                "branch-a": {"overall": {}},
                                                "branch-b": {"overall": {"1": "neutral"}},
                                            },
                                            "difference": {
                                                "branch-a": {"all": []},
                                                "branch-b": {
                                                    "all": [
                                                        {
                                                            "lower": 0.01,
                                                            "upper": 0.03,
                                                            "point": 0.02,
                                                        }
                                                    ]
                                                },
                                            },
                                        }
                                    }
                                }
                            },
                            "branch-b": {
                                "branch_data": {
                                    "other_metrics": {
                                        "urlbar_amazon_search_count": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 1.24,
                                                        "upper": 1.63,
                                                        "point": 1.43,
                                                    }
                                                ]
                                            },
                                            "relative_uplift": {
                                                "branch-a": {"all": [{}]},
                                                "branch-b": {"all": []},
                                            },
                                            "significance": {
                                                "branch-a": {
                                                    "overall": {"1": "positive"}
                                                },
                                                "branch-b": {"overall": {}},
                                            },
                                            "difference": {
                                                "branch-a": {
                                                    "all": [
                                                        {
                                                            "lower": 0.01,
                                                            "upper": 0.03,
                                                            "point": 0.02,
                                                        }
                                                    ]
                                                },
                                                "branch-b": {"all": []},
                                            },
                                        }
                                    }
                                }
                            },
                        }
                    }
                }
            }
        }
        self.experiment.save()

        results_a = self.results_manager.get_metric_data("enrollments", "all", "branch-a")
        results_b = self.results_manager.get_metric_data("enrollments", "all", "branch-b")

        data_a = (
            results_b.get(self.desktop_outcome_1.friendly_name, {})
            .get("data", {})
            .get("overall", {})
        )
        data_b = (
            results_a.get(self.desktop_outcome_1.friendly_name, {})
            .get("data", {})
            .get("overall", {})
        )

        self.assertEqual(
            data_a.get("urlbar_amazon_search_count").get("branch-a").get("absolute"),
            [{"lower": 1.49, "upper": 1.74, "significance": "neutral"}],
        )
        self.assertEqual(
            data_a.get("urlbar_amazon_search_count").get("branch-a").get("relative"),
            [
                {
                    "lower": -0.12,
                    "upper": 0.15,
                    "significance": "neutral",
                    "avg_rel_change": 0.02,
                }
            ],
        )

        self.assertEqual(
            data_b.get("urlbar_amazon_search_count").get("branch-b").get("absolute"),
            [{"lower": 1.24, "upper": 1.63, "significance": "positive"}],
        )

    @mock_valid_metrics
    def test_metric_areas_created_correctly(self):
        self.experiment.results_data = {
            "v3": {
                "other_metrics": {
                    "other_metrics": {
                        "mock_engagement_metric": "Metric Name",
                    }
                },
            }
        }
        self.experiment.save()

        MetricAreas.clear_cache()
        metric_areas = self.results_manager.get_metric_areas(
            "enrollments", "all", "branch-a"
        ).keys()

        self.assertIn("KPI Metrics", metric_areas)
        self.assertIn("Engagement", metric_areas)

    def test_get_branch_data_returns_correct_data(self):
        self.experiment.results_data = {
            "v3": {
                "overall": {
                    "enrollments": {
                        "all": {
                            "branch-a": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {"first": {"point": 150}},
                                            "percent": 12,
                                        }
                                    }
                                }
                            },
                            "branch-b": {
                                "branch_data": {
                                    "other_metrics": {
                                        "identity": {
                                            "absolute": {"first": {"point": 75}},
                                            "percent": 88,
                                        }
                                    }
                                }
                            },
                        }
                    }
                }
            }
        }
        self.experiment.save()

        result = self.results_manager.get_branch_data("enrollments", "all")

        self.assertEqual(len(result), 4)

        index_map = {item.get("slug"): i for i, item in enumerate(result)}
        first = result[index_map.get("branch-a")]
        second = result[index_map.get("branch-b")]

        # Validate first branch
        self.assertEqual(first["slug"], "branch-a")
        self.assertEqual(first["name"], "Branch A")
        self.assertEqual(first["percentage"], 12)
        self.assertEqual(first["num_participants"], 150)

        # Validate second branch
        self.assertEqual(second["slug"], "branch-b")
        self.assertEqual(second["name"], "Branch B")
        self.assertEqual(second["percentage"], 88)
        self.assertEqual(second["num_participants"], 75)

    @parameterized.expand(
        [
            (
                "client_level_daily_active_users_v2",
                [
                    {
                        "group": "other_metrics",
                        "friendly_name": "Retention",
                        "slug": "retained",
                        "description": "Percentage of users who returned to Firefox two weeks later.",  # noqa E501
                        "display_type": "percentage",
                    },
                    {
                        "group": "search_metrics",
                        "friendly_name": "Search Count",
                        "slug": "search_count",
                        "description": "Daily mean number of searches per user.",
                    },
                    {
                        "group": "other_metrics",
                        "friendly_name": "Daily Active Users",
                        "slug": "client_level_daily_active_users_v2",
                        "description": "Average number of client that sent a main ping per day.",  # noqa E501
                    },
                ],
            ),
            (
                "days_of_use",
                [
                    {
                        "group": "other_metrics",
                        "friendly_name": "Retention",
                        "slug": "retained",
                        "description": "Percentage of users who returned to Firefox two weeks later.",  # noqa E501
                        "display_type": "percentage",
                    },
                    {
                        "group": "search_metrics",
                        "friendly_name": "Search Count",
                        "slug": "search_count",
                        "description": "Daily mean number of searches per user.",
                    },
                    {
                        "group": "other_metrics",
                        "friendly_name": "Days of Use",
                        "slug": "days_of_use",
                        "description": "Average number of days each client sent a main ping.",  # noqa E501
                    },
                ],
            ),
        ]
    )
    def test_get_kpi_metrics_returns_correct_metrics(
        self, kpi_slug, expected_kpi_metrics
    ):
        self.experiment.results_data = {
            "v3": {
                "overall": {
                    "enrollments": {
                        "all": {
                            "branch-a": {
                                "branch_data": {
                                    "other_metrics": {
                                        kpi_slug: {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "lower": 1.19,
                                                        "upper": 1.74,
                                                        "point": 1.62,
                                                    }
                                                ]
                                            },
                                            "relative_uplift": {
                                                "branch-a": {"all": []},
                                                "branch-b": {
                                                    "all": [
                                                        {
                                                            "lower": -0.1,
                                                            "upper": 0.42,
                                                            "point": 0.2,
                                                        }
                                                    ]
                                                },
                                            },
                                            "significance": {
                                                "branch-a": {"overall": {}},
                                                "branch-b": {"overall": {"1": "neutral"}},
                                            },
                                            "difference": {
                                                "branch-a": {"all": []},
                                                "branch-b": {
                                                    "all": [
                                                        {
                                                            "lower": 0.01,
                                                            "upper": 0.03,
                                                            "point": 0.02,
                                                        }
                                                    ]
                                                },
                                            },
                                        }
                                    }
                                }
                            },
                        }
                    }
                }
            }
        }

        self.experiment.save()
        kpi_metrics = self.results_manager.get_kpi_metrics(
            "enrollments", "all", "branch-a"
        )

        self.assertListEqual(kpi_metrics, expected_kpi_metrics)

    def test_get_defaults_metrics_with_exclusions(self):
        self.experiment.results_data = {
            "v3": {
                "metadata": {
                    "metrics": {
                        "metricA": {
                            "retained": "Retained",
                            "search_count": "Search Count",
                        }
                    },
                },
                "other_metrics": {
                    "other_metrics": {
                        "retained": "2 Week Retention",
                        "search_count": "Search Count",
                    }
                },
            }
        }
        self.experiment.save()

        remaining_metrics = self.results_manager.get_remaining_metrics_metadata(
            exclude_slugs=["search_count"]
        )
        metric_slugs = [metric.get("slug") for metric in remaining_metrics]

        self.assertIn("retained", metric_slugs)
        self.assertNotIn("search_count", metric_slugs)

    @parameterized.expand(
        [
            (
                {
                    "v3": {
                        "overall": {
                            "enrollments": {
                                "all": {
                                    "branch-a": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "retained": {
                                                    "relative_uplift": {
                                                        "branch-a": {"all": []},
                                                        "branch-b": {
                                                            "all": [
                                                                {
                                                                    "lower": -0.12,
                                                                    "upper": 0.15,
                                                                    "point": 0.02,
                                                                }
                                                            ]
                                                        },
                                                        "branch-c": {
                                                            "all": [
                                                                {
                                                                    "lower": -0.1,
                                                                    "upper": 0.2,
                                                                    "point": 0.03,
                                                                }
                                                            ]
                                                        },
                                                    },
                                                }
                                            }
                                        }
                                    },
                                    "branch-b": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "retained": {
                                                    "relative_uplift": {
                                                        "branch-a": {
                                                            "all": [
                                                                {
                                                                    "lower": -2.3,
                                                                    "upper": 2.1,
                                                                    "point": 1.13,
                                                                }
                                                            ]
                                                        },
                                                        "branch-b": {"all": []},
                                                        "branch-c": {
                                                            "all": [
                                                                {
                                                                    "lower": -0.25,
                                                                    "upper": 0.45,
                                                                    "point": 0.1,
                                                                }
                                                            ]
                                                        },
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "branch-c": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "retained": {
                                                    "relative_uplift": {
                                                        "branch-a": {
                                                            "all": [
                                                                {
                                                                    "lower": -0.3,
                                                                    "upper": 1.68,
                                                                    "point": 1.458,
                                                                }
                                                            ]
                                                        },
                                                        "branch-b": {
                                                            "all": [
                                                                {
                                                                    "lower": -0.25,
                                                                    "upper": 0.45,
                                                                    "point": 0.1,
                                                                }
                                                            ]
                                                        },
                                                        "branch-c": {"all": []},
                                                    },
                                                }
                                            }
                                        }
                                    },
                                }
                            }
                        }
                    }
                },
                2.3,
            ),
            (
                {
                    "v3": {
                        "overall": {
                            "enrollments": {
                                "all": {
                                    "branch-a": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "retained": {
                                                    "relative_uplift": {
                                                        "branch-a": {"all": []},
                                                        "branch-b": {"all": [{}]},
                                                        "branch-c": {"all": [{}]},
                                                    },
                                                }
                                            }
                                        }
                                    },
                                    "branch-b": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "retained": {
                                                    "relative_uplift": {
                                                        "branch-a": {"all": [{}]},
                                                        "branch-b": {"all": []},
                                                        "branch-c": {"all": [{}]},
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "branch-c": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "retained": {
                                                    "relative_uplift": {
                                                        "branch-a": {"all": [{}]},
                                                        "branch-b": {"all": [{}]},
                                                        "branch-c": {"all": []},
                                                    },
                                                }
                                            }
                                        }
                                    },
                                }
                            }
                        }
                    }
                },
                0,
            ),
        ]
    )
    def test_get_max_metric_value(self, results_data, expected_max_value):
        NimbusBranchFactory.create(
            experiment=self.experiment, name="Branch C", slug="branch-c"
        )
        self.experiment.results_data = results_data

        extreme_retained = self.results_manager.get_max_metric_value(
            "enrollments", "all", "branch-a", "other_metrics", "retained"
        )
        self.assertEqual(extreme_retained, expected_max_value)

    def test_experiment_kpi_metrics_have_errors(self):
        self.experiment.results_data = {
            "v3": {
                "errors": {
                    "client_level_daily_active_users_v2": [
                        {"analysis_basis": "enrollments", "segment": "all"}
                    ],
                    "experiment": [],
                },
                "overall": {
                    "enrollments": {
                        "all": {
                            "branch-a": {
                                "branch_data": {
                                    "other_metrics": {
                                        "client_level_daily_active_users_v2": {
                                            "absolute": {"all": []},
                                            "difference": {
                                                "branch-a": {"all": [{}]},
                                            },
                                        }
                                    }
                                }
                            },
                        }
                    }
                },
            }
        }

        self.experiment.save()
        kpi_metrics = self.results_manager.get_kpi_metrics(
            "enrollments", "all", "branch-a"
        )

        self.assertIn(
            {
                "group": "other_metrics",
                "friendly_name": "Daily Active Users",
                "slug": "client_level_daily_active_users_v2",
                "description": "Average number of client that sent a main ping per day.",
                "has_errors": True,
            },
            kpi_metrics,
        )

    @parameterized.expand(
        [
            (
                {
                    "v3": {
                        "overall": {
                            "enrollments": {
                                "all": {
                                    "branch-a": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "urlbar_amazon_search_count": {
                                                    "absolute": {
                                                        "all": [
                                                            {
                                                                "lower": 1.49,
                                                                "upper": 1.74,
                                                                "point": 1.62,
                                                            }
                                                        ]
                                                    },
                                                    "percent": 12,
                                                }
                                            }
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
                "overall",
                {
                    "branch-a": {
                        "branch_data": {
                            "other_metrics": {
                                "urlbar_amazon_search_count": {
                                    "absolute": {
                                        "all": [
                                            {
                                                "lower": 1.49,
                                                "upper": 1.74,
                                                "point": 1.62,
                                            }
                                        ]
                                    },
                                    "percent": 12,
                                }
                            }
                        }
                    },
                },
            ),
            (
                {
                    "v3": {
                        "weekly": {
                            "enrollments": {
                                "all": {
                                    "branch-a": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "urlbar_amazon_search_count": {
                                                    "absolute": {
                                                        "all": [
                                                            {
                                                                "lower": 140,
                                                                "upper": 160,
                                                                "point": 150,
                                                            },
                                                            {
                                                                "lower": 130,
                                                                "upper": 150,
                                                                "point": 140,
                                                            },
                                                        ]
                                                    },
                                                }
                                            }
                                        },
                                    },
                                }
                            }
                        },
                        "overall": {
                            "enrollments": {
                                "all": {
                                    "branch-a": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "urlbar_amazon_search_count": {
                                                    "absolute": {
                                                        "all": [
                                                            {
                                                                "lower": 1.49,
                                                                "upper": 1.74,
                                                                "point": 1.62,
                                                            }
                                                        ]
                                                    },
                                                    "percent": 12,
                                                }
                                            }
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
                "weekly",
                {
                    "branch-a": {
                        "branch_data": {
                            "other_metrics": {
                                "urlbar_amazon_search_count": {
                                    "absolute": {
                                        "all": [
                                            {
                                                "lower": 140,
                                                "upper": 160,
                                                "point": 150,
                                            },
                                            {
                                                "lower": 130,
                                                "upper": 150,
                                                "point": 140,
                                            },
                                        ]
                                    },
                                }
                            }
                        },
                    },
                },
            ),
            (
                {
                    "v3": {
                        "weekly": None,
                        "overall": {
                            "enrollments": {
                                "all": {
                                    "branch-a": {
                                        "branch_data": {
                                            "other_metrics": {
                                                "urlbar_amazon_search_count": {
                                                    "absolute": {
                                                        "all": [
                                                            {
                                                                "lower": 1.49,
                                                                "upper": 1.74,
                                                                "point": 1.62,
                                                            }
                                                        ]
                                                    },
                                                    "percent": 12,
                                                }
                                            }
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
                "weekly",
                {},
            ),
        ]
    )
    def test_get_window_results(self, results_data, window, expected):
        self.experiment.results_data = results_data
        self.experiment.save()

        self.assertEqual(
            self.results_manager.get_window_results("enrollments", "all", window),
            expected,
        )
