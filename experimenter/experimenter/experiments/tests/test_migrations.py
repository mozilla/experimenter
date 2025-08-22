from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0289_alter_nimbusexperiment_firefox_labs_group",
    )
    migrate_to = (
        "experiments",
        "0290_draft_published_dto_to_none",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        User = self.old_state.apps.get_model("auth", "User")

        user = User.objects.create_user("user", "user@example.com", "password")

        NimbusExperiment.objects.create(
            name="draft-with-published-dto",
            slug="draft-with-published-dto",
            application=NimbusConstants.Application.DESKTOP,
            firefox_min_version=NimbusConstants.MIN_REQUIRED_VERSION,
            channel=NimbusConstants.Channel.NIGHTLY,
            owner=user,
            status=NimbusConstants.Status.DRAFT,
            status_next=None,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto={"some": "data"},
        )

        NimbusExperiment.objects.create(
            name="draft-without-published-dto",
            slug="draft-without-published-dto",
            application=NimbusConstants.Application.DESKTOP,
            firefox_min_version=NimbusConstants.MIN_REQUIRED_VERSION,
            channel=NimbusConstants.Channel.NIGHTLY,
            owner=user,
            status=NimbusConstants.Status.DRAFT,
            status_next=None,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto=None,
        )

        NimbusExperiment.objects.create(
            name="preview-with-published-dto",
            slug="preview-with-published-dto",
            application=NimbusConstants.Application.DESKTOP,
            firefox_min_version=NimbusConstants.MIN_REQUIRED_VERSION,
            channel=NimbusConstants.Channel.NIGHTLY,
            owner=user,
            status=NimbusConstants.Status.PREVIEW,
            status_next=None,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto={"preview": "data"},
        )

        NimbusExperiment.objects.create(
            name="live-with-published-dto",
            slug="live-with-published-dto",
            application=NimbusConstants.Application.DESKTOP,
            firefox_min_version=NimbusConstants.MIN_REQUIRED_VERSION,
            channel=NimbusConstants.Channel.NIGHTLY,
            owner=user,
            status=NimbusConstants.Status.LIVE,
            status_next=None,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto={"live": "data"},
        )

        NimbusExperiment.objects.create(
            name="complete-with-published-dto",
            slug="complete-with-published-dto",
            application=NimbusConstants.Application.DESKTOP,
            firefox_min_version=NimbusConstants.MIN_REQUIRED_VERSION,
            channel=NimbusConstants.Channel.NIGHTLY,
            owner=user,
            status=NimbusConstants.Status.COMPLETE,
            status_next=None,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto={"complete": "data"},
        )

    def test_migration_sets_draft_published_dto_to_none(self):
        """Test that migration sets published_dto to None for draft experiments only."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        draft_with_dto = NimbusExperiment.objects.get(slug="draft-with-published-dto")
        self.assertIsNone(draft_with_dto.published_dto)

        draft_without_dto = NimbusExperiment.objects.get(
            slug="draft-without-published-dto"
        )
        self.assertIsNone(draft_without_dto.published_dto)

        live_with_dto = NimbusExperiment.objects.get(slug="live-with-published-dto")
        self.assertEqual(live_with_dto.published_dto, {"live": "data"})

        preview_with_dto = NimbusExperiment.objects.get(slug="preview-with-published-dto")
        self.assertEqual(preview_with_dto.published_dto, {"preview": "data"})

        complete_with_dto = NimbusExperiment.objects.get(
            slug="complete-with-published-dto"
        )
        self.assertEqual(complete_with_dto.published_dto, {"complete": "data"})
