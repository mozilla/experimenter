import json

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0287_nimbusexperiment_channels",
    )
    migrate_to = (
        "experiments",
        "0288_nimbusexperiment_firefox_labs_description_links_text_field",
    )

    VALUES = {
        "empty-string": ['""', None],
        "null-as-string": ["null", None],
        "null-as-value": [None, None],
        "empty-object-as-string": ["{}", "{}"],
        "empty-object-as-value": [{}, "{}"],
        "object-as-string": [
            json.dumps({"foo": "bar"}),
            json.dumps({"foo": "bar"}),
        ],
        "object-as-value": [
            {"foo": "bar"},
            json.dumps({"foo": "bar"}),
        ],
        "list-as-string": ["[]", "[]"],
        "list-as-value": [[], "[]"],
        "string": ["bogus", '"bogus"'],
        "number-as-string": ["1", "1"],
        "number-as-value": [1, "1"],
    }

    def prepare(self):
        """Prepare some data before the migration."""
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        User = self.old_state.apps.get_model("auth", "User")

        user = User.objects.create_user("user", "user@example.com", "password")

        for slug, (before, _after) in self.VALUES.items():
            NimbusExperiment.objects.create(
                name=slug,
                slug=slug,
                application=NimbusConstants.Application.DESKTOP,
                firefox_min_version=NimbusConstants.MIN_REQUIRED_VERSION,
                channel=NimbusConstants.Channel.NIGHTLY,
                is_firefox_labs_opt_in=True,
                firefox_labs_title="test-title",
                firefox_labs_description="test-description",
                firefox_labs_description_links=before,
                firefox_labs_group="group",
                requires_restart=False,
                owner=user,
                status=NimbusConstants.Status.DRAFT,
                status_next=None,
                publish_status=NimbusConstants.PublishStatus.IDLE,
            )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        for slug, (before, after) in self.VALUES.items():
            experiment = NimbusExperiment.objects.get(slug=slug)

            self.assertEqual(
                experiment.firefox_labs_description_links,
                after,
                f"{slug}: {before!r} => {after!r}",
            )
