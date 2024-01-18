from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0254_auto_20240111_0418",
    )
    migrate_to = (
        "experiments",
        "0255_required_excluded_through",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        user = User.objects.create(email="test@example.com")

        parent_experiment = NimbusExperiment.objects.create(
            owner=user,
            name="test parent experiment",
            slug="test-parent-experiment",
            application=NimbusConstants.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto="{}",
        )
        required_experiment = NimbusExperiment.objects.create(
            owner=user,
            name="test required experiment",
            slug="test-required-experiment",
            application=NimbusConstants.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto="{}",
        )
        excluded_experiment = NimbusExperiment.objects.create(
            owner=user,
            name="test excluded experiment",
            slug="test-excluded-experiment",
            application=NimbusConstants.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto="{}",
        )
        parent_experiment.required_experiments.add(required_experiment)
        parent_experiment.excluded_experiments.add(excluded_experiment)

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        # Explicitly set through_fields on the related fields because of
        # a bug in django-test-migrations
        # https://github.com/wemake-services/django-test-migrations/issues/418
        required_field = next(
            f
            for f in NimbusExperiment._meta.many_to_many
            if f.name == "required_experiments"
        )
        excluded_field = next(
            f
            for f in NimbusExperiment._meta.many_to_many
            if f.name == "excluded_experiments"
        )
        required_field.remote_field.through_fields = (
            "parent_experiment",
            "child_experiment",
        )
        excluded_field.remote_field.through_fields = (
            "parent_experiment",
            "child_experiment",
        )

        parent_experiment = NimbusExperiment.objects.get(slug="test-parent-experiment")

        self.assertEqual(
            set(
                parent_experiment.required_experiments.all().values_list(
                    "slug", flat=True
                )
            ),
            {"test-required-experiment"},
        )
        self.assertEqual(
            set(
                parent_experiment.excluded_experiments.all().values_list(
                    "slug", flat=True
                )
            ),
            {"test-excluded-experiment"},
        )
