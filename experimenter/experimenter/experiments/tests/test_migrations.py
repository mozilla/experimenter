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
        self.assertDictEqual(changed_data["v2"], prechange_data["v2"])
        changes = changed_data["v3"]["weekly"]["enrollments"]["all"]

        changes_control = changes["control"]["branch_data"]["other_metrics"]["identity"]
        self.assertTrue("control" in changes_control["difference"])
        self.assertTrue("treatment" in changes_control["difference"])
        self.assertEqual(
            ["control", "treatment"], list(changes_control["difference"].keys())
        )
        self.assertFalse("all" in changes_control["difference"])
        self.assertFalse("first" in changes_control["difference"])
        self.assertTrue("all" in changes_control["difference"]["control"])
        self.assertTrue("first" in changes_control["difference"]["control"])
        self.assertTrue("all" in changes_control["difference"]["treatment"])
        self.assertTrue("first" in changes_control["difference"]["treatment"])
        self.assertFalse("point" in changes_control["difference"]["treatment"]["first"])

        self.assertTrue("control" in changes_control["relative_uplift"])
        self.assertTrue("treatment" in changes_control["relative_uplift"])
        self.assertFalse("all" in changes_control["relative_uplift"])
        self.assertFalse("first" in changes_control["relative_uplift"])
        self.assertFalse(
            "point" in changes_control["relative_uplift"]["treatment"]["first"]
        )

        self.assertTrue("control" in changes_control["significance"])
        self.assertTrue("treatment" in changes_control["significance"])
        self.assertFalse("weekly" in changes_control["significance"])
        self.assertFalse("overall" in changes_control["significance"])
        self.assertTrue("weekly" in changes_control["significance"]["treatment"])
        self.assertTrue("overall" in changes_control["significance"]["treatment"])
        self.assertFalse("1" in changes_control["significance"]["control"]["weekly"])

        changes_treatment = changes["treatment"]["branch_data"]["other_metrics"][
            "identity"
        ]
        self.assertTrue("control" in changes_treatment["difference"])
        self.assertTrue("treatment" in changes_treatment["difference"])
        self.assertFalse("all" in changes_treatment["difference"])
        self.assertFalse("first" in changes_treatment["difference"])
        self.assertEqual(
            ["all", "first"], list(changes_treatment["difference"]["control"].keys())
        )
        self.assertTrue("all" in changes_treatment["difference"]["control"])
        self.assertTrue("first" in changes_treatment["difference"]["control"])
        self.assertTrue("all" in changes_treatment["difference"]["treatment"])
        self.assertTrue("first" in changes_treatment["difference"]["treatment"])
        self.assertTrue("point" in changes_treatment["difference"]["control"]["first"])

        self.assertTrue("control" in changes_treatment["relative_uplift"])
        self.assertTrue("treatment" in changes_treatment["relative_uplift"])
        self.assertFalse("all" in changes_treatment["relative_uplift"])
        self.assertFalse("first" in changes_treatment["relative_uplift"])
        self.assertFalse(
            "point" in changes_treatment["relative_uplift"]["treatment"]["first"]
        )

        self.assertTrue("control" in changes_treatment["significance"])
        self.assertTrue("treatment" in changes_treatment["significance"])
        self.assertFalse("weekly" in changes_treatment["significance"])
        self.assertFalse("overall" in changes_treatment["significance"])
        self.assertTrue("weekly" in changes_treatment["significance"]["treatment"])
        self.assertTrue("overall" in changes_treatment["significance"]["treatment"])
        self.assertTrue("1" in changes_treatment["significance"]["control"]["weekly"])

        unchanged_data = NimbusExperiment.objects.get(
            slug="another-experiment"
        ).results_data
        nonchanges = unchanged_data["v3"]["weekly"]["enrollments"]["all"]["control"][
            "branch_data"
        ]["other_metrics"]["identity"]

        self.assertTrue("control" in nonchanges["difference"])
        self.assertTrue("treatment" in nonchanges["difference"])
        self.assertFalse("all" in nonchanges["difference"])
        self.assertFalse("first" in nonchanges["difference"])
        self.assertTrue("all" in nonchanges["difference"]["control"])
        self.assertTrue("first" in nonchanges["difference"]["control"])
        self.assertTrue("all" in nonchanges["difference"]["treatment"])
        self.assertTrue("first" in nonchanges["difference"]["treatment"])
        self.assertTrue("point" in nonchanges["difference"]["treatment"]["first"])

        self.assertTrue("control" in nonchanges["relative_uplift"])
        self.assertTrue("treatment" in nonchanges["relative_uplift"])
        self.assertFalse("all" in nonchanges["relative_uplift"])
        self.assertFalse("first" in nonchanges["relative_uplift"])
        self.assertFalse("point" in nonchanges["relative_uplift"]["control"]["first"])

        self.assertTrue("control" in nonchanges["significance"])
        self.assertTrue("treatment" in nonchanges["significance"])
        self.assertFalse("weekly" in nonchanges["significance"])
        self.assertFalse("overall" in nonchanges["significance"])
        self.assertTrue("1" in nonchanges["significance"]["treatment"]["weekly"])

        prechange_data = NimbusExperimentOld.objects.get(
            slug="another-experiment"
        ).results_data
        self.assertDictEqual(unchanged_data, prechange_data)
