from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0290_draft_published_dto_to_none",
    )
    migrate_to = (
        "experiments",
        "0291_desktop_channel_to_channels",
    )

    def prepare(self):
        """Prepare test data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        owner = User.objects.create()

        # Create desktop experiment with a channel
        self.desktop_with_channel = NimbusExperiment.objects.create(
            owner=owner,
            name="Desktop Nightly Experiment",
            slug="desktop-nightly",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.NIGHTLY,
            channels=[],
            status=NimbusConstants.Status.DRAFT,
        )

        # Create desktop experiment with no channel (draft status)
        self.desktop_no_channel = NimbusExperiment.objects.create(
            owner=owner,
            name="Desktop No Channel Experiment",
            slug="desktop-none",
            application=NimbusConstants.Application.DESKTOP,
            channel="",
            channels=[],
            status=NimbusConstants.Status.DRAFT,
        )

        # Create desktop experiment with no channel (live status)
        self.desktop_no_channel_active = NimbusExperiment.objects.create(
            owner=owner,
            name="Desktop No Channel Live Experiment",
            slug="desktop-live",
            application=NimbusConstants.Application.DESKTOP,
            channel="",
            channels=[],
            status=NimbusConstants.Status.LIVE,
        )

        # Create desktop experiment with no channel (complete status)
        self.desktop_no_channel_complete = NimbusExperiment.objects.create(
            owner=owner,
            name="Desktop No Channel Complete Experiment",
            slug="desktop-complete",
            application=NimbusConstants.Application.DESKTOP,
            channel="",
            channels=[],
            status=NimbusConstants.Status.COMPLETE,
        )

        # Create mobile experiment (should not be affected)
        self.mobile_experiment = NimbusExperiment.objects.create(
            owner=owner,
            name="Mobile Beta Experiment",
            slug="mobile-beta",
            application=NimbusConstants.Application.FENIX,
            channel=NimbusConstants.Channel.BETA,
            channels=[],
        )

    def test_migration(self):
        """Test the desktop channel to channels migration."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        # Test desktop experiment with channel gets migrated
        desktop_with_channel = NimbusExperiment.objects.get(slug="desktop-nightly")
        self.assertEqual(
            desktop_with_channel.channel, NimbusConstants.Channel.NO_CHANNEL
        )  # Should be NO_CHANNEL
        self.assertEqual(
            desktop_with_channel.channels, [NimbusConstants.Channel.NIGHTLY]
        )  # Should have channel in list

        # Test desktop experiment without channel stays empty
        desktop_no_channel = NimbusExperiment.objects.get(slug="desktop-none")
        self.assertEqual(desktop_no_channel.channel, NimbusConstants.Channel.NO_CHANNEL)
        self.assertEqual(desktop_no_channel.channels, [])  # Should remain empty

        # Test desktop experiment without channel but in active status gets all channels
        desktop_no_channel_active = NimbusExperiment.objects.get(slug="desktop-live")
        self.assertEqual(
            desktop_no_channel_active.channel, NimbusConstants.Channel.NO_CHANNEL
        )
        self.assertEqual(
            desktop_no_channel_active.channels,
            [
                NimbusConstants.Channel.UNBRANDED,
                NimbusConstants.Channel.NIGHTLY,
                NimbusConstants.Channel.BETA,
                NimbusConstants.Channel.RELEASE,
                NimbusConstants.Channel.ESR,
                NimbusConstants.Channel.AURORA,
            ],
        )  # Should get all desktop channels

        # Test desktop experiment without channel but in complete status gets all channels
        desktop_no_channel_complete = NimbusExperiment.objects.get(
            slug="desktop-complete"
        )
        self.assertEqual(
            desktop_no_channel_complete.channel, NimbusConstants.Channel.NO_CHANNEL
        )
        self.assertEqual(
            desktop_no_channel_complete.channels,
            [
                NimbusConstants.Channel.UNBRANDED,
                NimbusConstants.Channel.NIGHTLY,
                NimbusConstants.Channel.BETA,
                NimbusConstants.Channel.RELEASE,
                NimbusConstants.Channel.ESR,
                NimbusConstants.Channel.AURORA,
            ],
        )  # Should get all desktop channels

        # Test mobile experiment is unchanged
        mobile_experiment = NimbusExperiment.objects.get(slug="mobile-beta")
        self.assertEqual(mobile_experiment.channel, NimbusConstants.Channel.BETA)
        self.assertEqual(mobile_experiment.channels, [])
