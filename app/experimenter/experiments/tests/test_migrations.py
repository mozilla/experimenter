from django_test_migrations.contrib.unittest_case import MigratorTestCase


def create_experiment(experiment_model, branch_model, **data):
    experiment = experiment_model.objects.create(**data)
    experiment.reference_branch = branch_model.objects.create(
        experiment=experiment,
        name="control",
        slug="control",
    )
    experiment.save()
    branch_model.objects.create(
        experiment=experiment,
        name="treatment",
        slug="treatment",
    )
    return experiment


class TestMigration0181Forward(MigratorTestCase):
    migrate_from = ("experiments", "0195_nimbusexperiment_is_rollout")
    migrate_to = ("experiments", "0196_nimbusbranch_feature_enabled")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusBranch = self.old_state.apps.get_model("experiments", "NimbusBranch")

        owner = User.objects.create(username="owner")

        create_experiment(
            NimbusExperiment,
            NimbusBranch,
            owner=owner,
            name="with_dto",
            slug="with_dto",
            published_dto={
                "branches": [
                    {
                        "feature": {
                            "enabled": False,
                            "featureId": "abouthomecache",
                            "value": {},
                        },
                        "ratio": 1,
                        "slug": "control",
                    },
                    {
                        "feature": {
                            "enabled": True,
                            "featureId": "abouthomecache",
                            "value": {},
                        },
                        "ratio": 1,
                        "slug": "treatment",
                    },
                ],
            },
        )

        self.invalid_experiments = [
            create_experiment(
                NimbusExperiment,
                NimbusBranch,
                owner=owner,
                name="no_dto",
                slug="no_dto",
                published_dto=None,
            ),
            create_experiment(
                NimbusExperiment,
                NimbusBranch,
                owner=owner,
                name="empty_dto",
                slug="empty_dto",
                published_dto={},
            ),
            create_experiment(
                NimbusExperiment,
                NimbusBranch,
                owner=owner,
                name="with_branch_slug_mismatch",
                slug="with_branch_slug_mismatch",
                published_dto={
                    "branches": [
                        {
                            "feature": {
                                "enabled": False,
                                "featureId": "abouthomecache",
                                "value": {},
                            },
                            "ratio": 1,
                            "slug": "wrong_control",
                        },
                        {
                            "feature": {
                                "enabled": True,
                                "featureId": "abouthomecache",
                                "value": {},
                            },
                            "ratio": 1,
                            "slug": "wrong_treatment",
                        },
                    ],
                },
            ),
            create_experiment(
                NimbusExperiment,
                NimbusBranch,
                owner=owner,
                name="with_empty_branches",
                slug="with_empty_branches",
                published_dto={
                    "branches": [
                        {},
                        {},
                    ],
                },
            ),
            create_experiment(
                NimbusExperiment,
                NimbusBranch,
                owner=owner,
                name="with_empty_features",
                slug="with_empty_features",
                published_dto={
                    "branches": [
                        {
                            "feature": {},
                            "ratio": 1,
                            "slug": "control",
                        },
                        {
                            "feature": {},
                            "ratio": 1,
                            "slug": "treatment",
                        },
                    ],
                },
            ),
        ]

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        experiment_with_dto = NimbusExperiment.objects.get(slug="with_dto")
        self.assertEqual(
            experiment_with_dto.branches.get(slug="control").feature_enabled, False
        )
        self.assertEqual(
            experiment_with_dto.branches.get(slug="treatment").feature_enabled, True
        )

        for old_experiment in self.invalid_experiments:
            new_experiment = NimbusExperiment.objects.get(slug=old_experiment.slug)
            self.assertFalse(
                new_experiment.branches.filter(feature_enabled=False).exists(),
            )
