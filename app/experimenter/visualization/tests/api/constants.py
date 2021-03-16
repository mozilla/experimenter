from experimenter.visualization.api.v3.views import Significance


class TestConstants:
    @classmethod
    def get_test_data(cls):
        DATA_IDENTITY_ROW = {
            "point": 12,
            "upper": 13,
            "lower": 10,
            "metric": "identity",
            "statistic": "count",
            "window_index": "1",
        }
        CONTROL_DATA_ROW = {
            **DATA_IDENTITY_ROW,
            **{
                "branch": "control",
            },
        }
        VARIANT_DATA_ROW = {
            **DATA_IDENTITY_ROW,
            **{
                "branch": "variant",
            },
        }
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN = {
            **DATA_IDENTITY_ROW,
            **{
                "metric": "some_count",
                "statistic": "mean",
                "branch": "variant",
            },
        }
        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL = {
            **DATA_IDENTITY_ROW,
            **{
                "metric": "another_count",
                "statistic": "binomial",
                "branch": "variant",
            },
        }
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW = {
            **DATA_IDENTITY_ROW,
            **{
                "comparison": "difference",
                "metric": "search_count",
                "statistic": "mean",
                "branch": "variant",
            },
        }
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW = {
            **VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW,
            **{
                "point": -2,
                "upper": -1,
                "lower": -5,
                "metric": "retained",
                "statistic": "binomial",
            },
        }
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW = {
            **VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            **{
                "point": 12,
                "upper": 13,
                "lower": -5,
                "branch": "control",
            },
        }
        DATA_WITHOUT_POPULATION_PERCENTAGE = [
            CONTROL_DATA_ROW,
            VARIANT_DATA_ROW,
            VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN,
            VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL,
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW,
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ]

        FORMATTED_DATA_WITHOUT_POPULATION_PERCENTAGE = {
            "control": {
                "is_control": False,
                "branch_data": {
                    "identity": {
                        "absolute": {
                            "first": {
                                "lower": 10,
                                "point": 12,
                                "upper": 13,
                                "window_index": "1",
                            },
                            "all": [
                                {
                                    "lower": 10,
                                    "point": 12,
                                    "upper": 13,
                                    "window_index": "1",
                                }
                            ],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                    },
                    "retained": {
                        "absolute": {"all": [], "first": {}},
                        "difference": {
                            "all": [
                                {
                                    "point": 12,
                                    "upper": 13,
                                    "lower": -5,
                                    "window_index": "1",
                                }
                            ],
                            "first": {
                                "point": 12,
                                "upper": 13,
                                "lower": -5,
                                "window_index": "1",
                            },
                        },
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {
                            "overall": {},
                            "weekly": {"1": Significance.NEUTRAL},
                        },
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    "identity": {
                        "absolute": {
                            "first": {
                                "lower": 10,
                                "point": 12,
                                "upper": 13,
                                "window_index": "1",
                            },
                            "all": [
                                {
                                    "lower": 10,
                                    "point": 12,
                                    "upper": 13,
                                    "window_index": "1",
                                }
                            ],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                    },
                    "search_count": {
                        "absolute": {"all": [], "first": {}},
                        "difference": {
                            "first": {
                                "lower": 10,
                                "point": 12,
                                "upper": 13,
                                "window_index": "1",
                            },
                            "all": [
                                {
                                    "lower": 10,
                                    "point": 12,
                                    "upper": 13,
                                    "window_index": "1",
                                }
                            ],
                        },
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {
                            "overall": {},
                            "weekly": {"1": Significance.POSITIVE},
                        },
                    },
                    "some_count": {
                        "absolute": {
                            "first": {
                                "lower": 10,
                                "point": 12,
                                "upper": 13,
                                "window_index": "1",
                            },
                            "all": [
                                {
                                    "lower": 10,
                                    "point": 12,
                                    "upper": 13,
                                    "window_index": "1",
                                }
                            ],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                    },
                    "another_count": {
                        "absolute": {
                            "first": {
                                "lower": 10,
                                "point": 12,
                                "upper": 13,
                                "window_index": "1",
                            },
                            "all": [
                                {
                                    "lower": 10,
                                    "point": 12,
                                    "upper": 13,
                                    "window_index": "1",
                                }
                            ],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                    },
                    "retained": {
                        "absolute": {"all": [], "first": {}},
                        "difference": {
                            "first": {
                                "point": -2,
                                "upper": -1,
                                "lower": -5,
                                "window_index": "1",
                            },
                            "all": [
                                {
                                    "point": -2,
                                    "upper": -1,
                                    "lower": -5,
                                    "window_index": "1",
                                }
                            ],
                        },
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {
                            "overall": {},
                            "weekly": {"1": Significance.NEGATIVE},
                        },
                    },
                },
            },
        }

        FORMATTED_DATA_WITH_POPULATION_PERCENTAGE = {
            "control": {
                "is_control": False,
                "branch_data": {
                    "identity": {
                        "absolute": {
                            "first": {"lower": 10, "point": 12, "upper": 13},
                            "all": [{"lower": 10, "point": 12, "upper": 13}],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                        "percent": 50,
                    },
                    "retained": {
                        "absolute": {"all": [], "first": {}},
                        "difference": {
                            "all": [
                                {
                                    "point": 12,
                                    "upper": 13,
                                    "lower": -5,
                                },
                                {
                                    "point": 12,
                                    "upper": 13,
                                    "lower": -5,
                                },
                            ],
                            "first": {
                                "point": 12,
                                "upper": 13,
                                "lower": -5,
                            },
                        },
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {
                            "overall": {"1": Significance.NEUTRAL},
                            "weekly": {},
                        },
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    "identity": {
                        "absolute": {
                            "first": {"lower": 10, "point": 12, "upper": 13},
                            "all": [{"lower": 10, "point": 12, "upper": 13}],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                        "percent": 50,
                    },
                    "search_count": {
                        "absolute": {"all": [], "first": {}},
                        "difference": {
                            "first": {"lower": 10, "point": 12, "upper": 13},
                            "all": [{"lower": 10, "point": 12, "upper": 13}],
                        },
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {
                            "overall": {"1": Significance.POSITIVE},
                            "weekly": {},
                        },
                    },
                    "some_count": {
                        "absolute": {
                            "first": {"lower": 10, "point": 12, "upper": 13},
                            "all": [{"lower": 10, "point": 12, "upper": 13}],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                    },
                    "another_count": {
                        "absolute": {
                            "first": {"lower": 10, "point": 12, "upper": 13},
                            "all": [{"lower": 10, "point": 12, "upper": 13}],
                        },
                        "difference": {"all": [], "first": {}},
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {"overall": {}, "weekly": {}},
                    },
                    "retained": {
                        "absolute": {"all": [], "first": {}},
                        "difference": {
                            "first": {
                                "point": -2,
                                "upper": -1,
                                "lower": -5,
                            },
                            "all": [
                                {
                                    "point": -2,
                                    "upper": -1,
                                    "lower": -5,
                                },
                                {
                                    "point": -2,
                                    "upper": -1,
                                    "lower": -5,
                                },
                            ],
                        },
                        "relative_uplift": {"all": [], "first": {}},
                        "significance": {
                            "overall": {"1": Significance.NEGATIVE},
                            "weekly": {},
                        },
                    },
                },
            },
        }

        return (
            DATA_WITHOUT_POPULATION_PERCENTAGE,
            FORMATTED_DATA_WITHOUT_POPULATION_PERCENTAGE,
            FORMATTED_DATA_WITH_POPULATION_PERCENTAGE,
        )
