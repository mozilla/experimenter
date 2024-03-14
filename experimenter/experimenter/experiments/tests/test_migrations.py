from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment as Experiment


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0265_alter_nimbusexperimentbranchthroughexcluded_child_experiment_and_more",
    )
    migrate_to = (
        "experiments",
        "0266_nimbusexperiment_results_pairwise_data",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusBranch = self.old_state.apps.get_model("experiments", "NimbusBranch")
        user = User.objects.create(email="test@example.com")

        empty_data_point = {"all": [], "first": {}}
        data_point = {"all": [{"point": 1}, {"point": 2}], "first": {"point": 1}}

        empty_significance = {"weekly": {}, "overall": {}}
        significance = {"weekly": {"1": "positive"}, "overall": {}}

        old_data = {
            "enrollments": {
                "all": {
                    "control": {
                        "is_control": True,
                        "branch_data": {
                            "other_metrics": {
                                "identity": {
                                    "absolute": data_point,
                                    "difference": data_point,
                                    "relative_uplift": data_point,
                                    "significance": significance,
                                    "percent": 0.0,
                                }
                            }
                        },
                    },
                    "treatment": {
                        "is_control": True,
                        "branch_data": {
                            "other_metrics": {
                                "identity": {
                                    "absolute": data_point,
                                    "difference": data_point,
                                    "relative_uplift": data_point,
                                    "significance": significance,
                                    "percent": 0.0,
                                }
                            }
                        },
                    },
                }
            }
        }

        # create experiment with old results data
        old = NimbusExperiment.objects.create(
            owner=user,
            name="test experiment",
            slug="test-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            results_data={
                "v2": {
                    "daily": {},
                    "weekly": old_data,
                    "overall": old_data,
                    "other_metrics": {},
                    "metadata": {},
                    "show_analysis": True,
                    "errors": [],
                },
            },
        )
        reference_branch = NimbusBranch.objects.create(
            slug="control", experiment_id=old.id
        )
        NimbusBranch.objects.create(slug="treatment", experiment_id=old.id)
        old.reference_branch = reference_branch

        new_data = {
            "enrollments": {
                "all": {
                    "control": {
                        "is_control": True,
                        "branch_data": {
                            "other_metrics": {
                                "identity": {
                                    "absolute": data_point,
                                    "difference": {
                                        "control": empty_data_point,
                                        "treatment": data_point,
                                    },
                                    "relative_uplift": {
                                        "control": empty_data_point,
                                        "treatment": data_point,
                                    },
                                    "significance": {
                                        "control": empty_significance,
                                        "treatment": significance,
                                    },
                                    "percent": 0.0,
                                }
                            }
                        },
                    },
                    "treatment": {
                        "is_control": True,
                        "branch_data": {
                            "other_metrics": {
                                "identity": {
                                    "absolute": data_point,
                                    "difference": {
                                        "control": data_point,
                                        "treatment": empty_data_point,
                                    },
                                    "relative_uplift": {
                                        "control": data_point,
                                        "treatment": empty_data_point,
                                    },
                                    "significance": {
                                        "control": significance,
                                        "treatment": empty_significance,
                                    },
                                    "percent": 0.0,
                                }
                            }
                        },
                    },
                }
            }
        }

        # create experiment with new results data
        new = NimbusExperiment.objects.create(
            owner=user,
            name="another experiment",
            slug="another-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            results_data={
                "v2": {
                    "daily": {},
                    "weekly": old_data,
                    "overall": old_data,
                    "other_metrics": {},
                    "metadata": {},
                    "show_analysis": True,
                    "errors": [],
                },
                "v3": {
                    "daily": {},
                    "weekly": new_data,
                    "overall": new_data,
                    "other_metrics": {},
                    "metadata": {},
                    "show_analysis": True,
                    "errors": [],
                },
            },
        )
        reference_branch = NimbusBranch.objects.create(
            slug="control", experiment_id=new.id
        )
        NimbusBranch.objects.create(slug="treatment", experiment_id=new.id)
        new.reference_branch = reference_branch

        # create experiment with empty (but not None) results
        empty = NimbusExperiment.objects.create(
            owner=user,
            name="empty experiment",
            slug="empty-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            results_data={},
        )
        reference_branch = NimbusBranch.objects.create(
            slug="control", experiment_id=empty.id
        )
        NimbusBranch.objects.create(slug="treatment", experiment_id=empty.id)
        empty.reference_branch = reference_branch

    def test_migration(self):
        """Run the test itself."""
        NimbusExperimentOld = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        prechange_data = NimbusExperimentOld.objects.get(
            slug="test-experiment"
        ).results_data
        changed_data = NimbusExperiment.objects.get(slug="test-experiment").results_data
        self.assertEqual(changed_data["v2"], prechange_data["v2"])
        changes = changed_data["v3"]["weekly"]["enrollments"]["all"]

        changes_control = changes["control"]["branch_data"]["other_metrics"]["identity"]
        self.assertIn("percent", changes_control)

        self.assertIn("control", changes_control["difference"])
        self.assertIn("treatment", changes_control["difference"])
        self.assertEqual(
            ["control", "treatment"], list(changes_control["difference"].keys())
        )
        self.assertNotIn("all", changes_control["difference"])
        self.assertNotIn("first", changes_control["difference"])
        self.assertIn("all", changes_control["difference"]["control"])
        self.assertIn("first", changes_control["difference"]["control"])
        self.assertIn("all", changes_control["difference"]["treatment"])
        self.assertIn("first", changes_control["difference"]["treatment"])
        self.assertNotIn("point", changes_control["difference"]["treatment"]["first"])

        self.assertIn("control", changes_control["relative_uplift"])
        self.assertIn("treatment", changes_control["relative_uplift"])
        self.assertNotIn("all", changes_control["relative_uplift"])
        self.assertNotIn("first", changes_control["relative_uplift"])
        self.assertNotIn(
            "point", changes_control["relative_uplift"]["treatment"]["first"]
        )

        self.assertIn("control", changes_control["significance"])
        self.assertIn("treatment", changes_control["significance"])
        self.assertNotIn("weekly", changes_control["significance"])
        self.assertNotIn("overall", changes_control["significance"])
        self.assertIn("weekly", changes_control["significance"]["treatment"])
        self.assertIn("overall", changes_control["significance"]["treatment"])
        self.assertNotIn("1", changes_control["significance"]["control"]["weekly"])

        changes_treatment = changes["treatment"]["branch_data"]["other_metrics"][
            "identity"
        ]
        self.assertIn("percent", changes_treatment)
        self.assertIn("control", changes_treatment["difference"])
        self.assertIn("treatment", changes_treatment["difference"])
        self.assertNotIn("all", changes_treatment["difference"])
        self.assertNotIn("first", changes_treatment["difference"])
        self.assertEqual(
            ["all", "first"], list(changes_treatment["difference"]["control"].keys())
        )
        self.assertIn("all", changes_treatment["difference"]["control"])
        self.assertIn("first", changes_treatment["difference"]["control"])
        self.assertIn("all", changes_treatment["difference"]["treatment"])
        self.assertIn("first", changes_treatment["difference"]["treatment"])
        self.assertIn("point", changes_treatment["difference"]["control"]["first"])

        self.assertIn("control", changes_treatment["relative_uplift"])
        self.assertIn("treatment", changes_treatment["relative_uplift"])
        self.assertNotIn("all", changes_treatment["relative_uplift"])
        self.assertNotIn("first", changes_treatment["relative_uplift"])
        self.assertNotIn(
            "point", changes_treatment["relative_uplift"]["treatment"]["first"]
        )

        self.assertIn("control", changes_treatment["significance"])
        self.assertIn("treatment", changes_treatment["significance"])
        self.assertNotIn("weekly", changes_treatment["significance"])
        self.assertNotIn("overall", changes_treatment["significance"])
        self.assertIn("weekly", changes_treatment["significance"]["treatment"])
        self.assertIn("overall", changes_treatment["significance"]["treatment"])
        self.assertIn("1", changes_treatment["significance"]["control"]["weekly"])

        unchanged_data = NimbusExperiment.objects.get(
            slug="another-experiment"
        ).results_data
        nonchanges = unchanged_data["v3"]["weekly"]["enrollments"]["all"]["control"][
            "branch_data"
        ]["other_metrics"]["identity"]

        self.assertIn("control", nonchanges["difference"])
        self.assertIn("treatment", nonchanges["difference"])
        self.assertNotIn("all", nonchanges["difference"])
        self.assertNotIn("first", nonchanges["difference"])
        self.assertIn("all", nonchanges["difference"]["control"])
        self.assertIn("first", nonchanges["difference"]["control"])
        self.assertIn("all", nonchanges["difference"]["treatment"])
        self.assertIn("first", nonchanges["difference"]["treatment"])
        self.assertIn("point", nonchanges["difference"]["treatment"]["first"])

        self.assertIn("control", nonchanges["relative_uplift"])
        self.assertIn("treatment", nonchanges["relative_uplift"])
        self.assertNotIn("all", nonchanges["relative_uplift"])
        self.assertNotIn("first", nonchanges["relative_uplift"])
        self.assertNotIn("point", nonchanges["relative_uplift"]["control"]["first"])

        self.assertIn("control", nonchanges["significance"])
        self.assertIn("treatment", nonchanges["significance"])
        self.assertNotIn("weekly", nonchanges["significance"])
        self.assertNotIn("overall", nonchanges["significance"])
        self.assertIn("1", nonchanges["significance"]["treatment"]["weekly"])

        prechange_data = NimbusExperimentOld.objects.get(
            slug="another-experiment"
        ).results_data
        self.assertEqual(unchanged_data, prechange_data)

        unchanged_data = NimbusExperiment.objects.get(
            slug="empty-experiment"
        ).results_data
        prechange_data = NimbusExperimentOld.objects.get(
            slug="empty-experiment"
        ).results_data
        self.assertEqual(unchanged_data, prechange_data)
