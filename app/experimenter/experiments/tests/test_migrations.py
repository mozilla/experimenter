from django.utils.text import slugify
from django_test_migrations.contrib.unittest_case import MigratorTestCase
from faker import Factory as FakerFactory

from experimenter.experiments.constants import NimbusConstants

faker = FakerFactory.create()


def create_experiments(User, NimbusExperiment, *args):
    owner = User.objects.create(
        first_name="foo",
        last_name="bar",
        email="foo@example.com",
        username="foobar",
    )
    return [
        NimbusExperiment.objects.create(
            name=faker.catch_phrase(),
            slug=slugify(faker.catch_phrase())[: NimbusConstants.MAX_SLUG_LEN],
            owner=owner,
            **props,
        ).id
        for props in args
    ]


class TestMigration0174Forward(MigratorTestCase):
    migrate_from = ("experiments", "0174_nimbusexperiment_results_data")
    migrate_to = ("experiments", "0175_switch_to_status_next")

    def prepare(self):
        """Prepare some data before the migration."""
        self.experiment_ids = create_experiments(
            self.old_state.apps.get_model("auth", "User"),
            self.old_state.apps.get_model("experiments", "NimbusExperiment"),
            dict(
                status=NimbusConstants.Status.DRAFT,
                publish_status=NimbusConstants.PublishStatus.REVIEW,
            ),
            dict(
                status=NimbusConstants.Status.DRAFT,
                publish_status=NimbusConstants.PublishStatus.IDLE,
            ),
            dict(
                status=NimbusConstants.Status.LIVE,
                publish_status=NimbusConstants.PublishStatus.REVIEW,
                is_end_requested=True,
            ),
            dict(
                status=NimbusConstants.Status.LIVE,
                publish_status=NimbusConstants.PublishStatus.APPROVED,
                is_end_requested=False,
            ),
            dict(
                status=NimbusConstants.Status.COMPLETE,
                publish_status=NimbusConstants.PublishStatus.IDLE,
                is_end_requested=True,
            ),
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        expected_status_next_values = (
            NimbusConstants.Status.LIVE,
            None,
            NimbusConstants.Status.COMPLETE,
            NimbusConstants.Status.LIVE,
            None,
        )
        for experiment_id, expected_status_next in zip(
            self.experiment_ids, expected_status_next_values
        ):
            self.assertEqual(
                NimbusExperiment.objects.get(id=experiment_id).status_next,
                expected_status_next,
            )


class TestMigration0174Backward(MigratorTestCase):
    migrate_from = ("experiments", "0175_switch_to_status_next")
    migrate_to = ("experiments", "0174_nimbusexperiment_results_data")

    def prepare(self):
        """Prepare some data before the migration."""
        self.experiment_ids = create_experiments(
            self.old_state.apps.get_model("auth", "User"),
            self.old_state.apps.get_model("experiments", "NimbusExperiment"),
            dict(
                status=NimbusConstants.Status.LIVE,
                status_next=NimbusConstants.Status.COMPLETE,
            ),
            # Invalid, but shouldn't match query
            dict(
                status=NimbusConstants.Status.COMPLETE,
                status_next=NimbusConstants.Status.COMPLETE,
            ),
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        expected_is_end_requested_values = (
            True,
            False,
        )
        for experiment_id, expected_is_end_requested in zip(
            self.experiment_ids, expected_is_end_requested_values
        ):
            self.assertEqual(
                NimbusExperiment.objects.get(id=experiment_id).is_end_requested,
                expected_is_end_requested,
            )
