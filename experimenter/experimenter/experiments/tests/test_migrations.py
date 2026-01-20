from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestResultsV3OverallDictMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0314_nimbusexperiment_risk_ai",
    )
    migrate_to = (
        "experiments",
        "0315_results_v3_overall_dict",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        owner, _ = User.objects.get_or_create(
            username="test@example.com",
            defaults={"email": "test@example.com"},
        )

        results_data_broken = {
            "v3": {
                "overall": {
                    "enrollments": {
                        "all": {
                            "control": {
                                "is_control": True,
                                "branch_data": {
                                    "identity": {
                                        "retention": {
                                            "absolute": {"all": [], "first": {}},
                                            "difference": {
                                                "treatment": {"all": [], "first": {}}
                                            },
                                            "relative_uplift": {
                                                "treatment": {"all": [], "first": {}}
                                            },
                                            "significance": {
                                                "treatment": {
                                                    "weekly": {},
                                                    "overall": [],
                                                }
                                            },
                                            "percent": 0.0,
                                        }
                                    }
                                },
                            },
                            "treatment": {
                                "is_control": False,
                                "branch_data": {
                                    "identity": {
                                        "retention": {
                                            "absolute": {"all": [], "first": {}},
                                            "difference": {
                                                "control": {"all": [], "first": {}}
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}}
                                            },
                                            "significance": {
                                                "control": {
                                                    "weekly": {},
                                                    "overall": [],
                                                }
                                            },
                                            "percent": 0.0,
                                        }
                                    }
                                },
                            },
                        }
                    }
                }
            }
        }

        results_data_healthy = {
            "v3": {
                "overall": {
                    "enrollments": {
                        "all": {
                            "control": {
                                "is_control": True,
                                "branch_data": {
                                    "identity": {
                                        "retention": {
                                            "absolute": {"all": [], "first": {}},
                                            "difference": {
                                                "treatment": {"all": [], "first": {}}
                                            },
                                            "relative_uplift": {
                                                "treatment": {"all": [], "first": {}}
                                            },
                                            "significance": {
                                                "treatment": {
                                                    "weekly": {},
                                                    "overall": {},
                                                }
                                            },
                                            "percent": 0.0,
                                        }
                                    }
                                },
                            },
                            "treatment": {
                                "is_control": False,
                                "branch_data": {
                                    "identity": {
                                        "retention": {
                                            "absolute": {"all": [], "first": {}},
                                            "difference": {
                                                "control": {"all": [], "first": {}}
                                            },
                                            "relative_uplift": {
                                                "control": {"all": [], "first": {}}
                                            },
                                            "significance": {
                                                "control": {
                                                    "weekly": {},
                                                    "overall": {},
                                                }
                                            },
                                            "percent": 0.0,
                                        }
                                    }
                                },
                            },
                        }
                    }
                }
            }
        }

        NimbusExperiment.objects.create(
            slug="test-experiment-broken",
            name="Test Experiment Broken",
            application="fenix",
            owner=owner,
            results_data=results_data_broken,
        )

        NimbusExperiment.objects.create(
            slug="test-experiment-healthy",
            name="Test Experiment Healthy",
            application="fenix",
            owner=owner,
            results_data=results_data_healthy,
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        experiment_broken = NimbusExperiment.objects.get(slug="test-experiment-broken")

        control_significance = experiment_broken.results_data["v3"]["overall"][
            "enrollments"
        ]["all"]["control"]["branch_data"]["identity"]["retention"]["significance"]
        self.assertEqual(control_significance["treatment"]["overall"], {})
        self.assertNotEqual(control_significance["treatment"]["overall"], [])

        treatment_significance = experiment_broken.results_data["v3"]["overall"][
            "enrollments"
        ]["all"]["treatment"]["branch_data"]["identity"]["retention"]["significance"]
        self.assertEqual(treatment_significance["control"]["overall"], {})
        self.assertNotEqual(treatment_significance["control"]["overall"], [])

        experiment_healthy = NimbusExperiment.objects.get(slug="test-experiment-healthy")
        control_significance_healthy = experiment_healthy.results_data["v3"]["overall"][
            "enrollments"
        ]["all"]["control"]["branch_data"]["identity"]["retention"]["significance"]
        self.assertEqual(control_significance_healthy["treatment"]["overall"], {})

        treatment_significance_healthy = experiment_healthy.results_data["v3"]["overall"][
            "enrollments"
        ]["all"]["treatment"]["branch_data"]["identity"]["retention"]["significance"]
        self.assertEqual(treatment_significance_healthy["control"]["overall"], {})
