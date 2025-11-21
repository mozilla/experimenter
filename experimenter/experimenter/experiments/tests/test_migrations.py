from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestFirefoxMinVersionParsedMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0301_alter_nimbusdocumentationlink_title",
    )
    migrate_to = (
        "experiments",
        "0302_nimbusexperiment_firefox_min_version_parsed",
    )

    def prepare(self):
        """Prepare test data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        owner = User.objects.create()

        self.experiment_with_bang = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with ! version",
            slug="experiment-with-bang",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.DRAFT,
            firefox_min_version="95.!",
        )

        self.experiment_with_semver = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with semver",
            slug="experiment-with-semver",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.BETA,
            status=NimbusConstants.Status.DRAFT,
            firefox_min_version="92.0.1",
        )

        self.experiment_with_empty = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with empty version",
            slug="experiment-with-empty",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.RELEASE,
            status=NimbusConstants.Status.DRAFT,
            firefox_min_version="",
        )

        self.experiment_with_major_minor = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with major.minor",
            slug="experiment-with-major-minor",
            application=NimbusConstants.Application.FENIX,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.DRAFT,
            firefox_min_version="100.1.0",
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        experiment_bang = NimbusExperiment.objects.get(slug="experiment-with-bang")
        self.assertEqual(experiment_bang._firefox_min_version_parsed, [95, 0, 0])

        experiment_semver = NimbusExperiment.objects.get(slug="experiment-with-semver")
        self.assertEqual(experiment_semver._firefox_min_version_parsed, [92, 0, 1])

        experiment_empty = NimbusExperiment.objects.get(slug="experiment-with-empty")
        self.assertEqual(experiment_empty._firefox_min_version_parsed, [0, 0, 0])

        experiment_full = NimbusExperiment.objects.get(slug="experiment-with-major-minor")
        self.assertEqual(experiment_full._firefox_min_version_parsed, [100, 1, 0])

        experiments = list(
            NimbusExperiment.objects.all().order_by("_firefox_min_version_parsed")
        )
        self.assertEqual(experiments[0].slug, "experiment-with-empty")
        self.assertEqual(experiments[1].slug, "experiment-with-semver")
        self.assertEqual(experiments[2].slug, "experiment-with-bang")
        self.assertEqual(experiments[3].slug, "experiment-with-major-minor")


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0297_nimbusfeatureconfig_subscribers",
    )
    migrate_to = (
        "experiments",
        "0298_convert_projects_to_tags",
    )

    def prepare(self):
        """Prepare test data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        Project = self.old_state.apps.get_model("projects", "Project")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        owner = User.objects.create()

        # Create test projects
        self.project1 = Project.objects.create(
            name="Firefox Desktop", slug="firefox-desktop"
        )
        self.project2 = Project.objects.create(
            name="Mobile Performance", slug="mobile-performance"
        )
        self.project3 = Project.objects.create(
            name="Privacy Features", slug="privacy-features"
        )

        # Create experiments with projects
        self.experiment1 = NimbusExperiment.objects.create(
            owner=owner,
            name="Desktop Feature Test",
            slug="desktop-feature-test",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.DRAFT,
        )
        self.experiment1.projects.add(self.project1, self.project3)

        self.experiment2 = NimbusExperiment.objects.create(
            owner=owner,
            name="Mobile Performance Test",
            slug="mobile-performance-test",
            application=NimbusConstants.Application.FENIX,
            channel=NimbusConstants.Channel.BETA,
            status=NimbusConstants.Status.DRAFT,
        )
        self.experiment2.projects.add(self.project2)

        # Create experiment with no projects
        self.experiment3 = NimbusExperiment.objects.create(
            owner=owner,
            name="No Project Experiment",
            slug="no-project-experiment",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.RELEASE,
            status=NimbusConstants.Status.DRAFT,
        )

    def test_migration(self):
        """Test the projects to tags conversion migration."""
        Tag = self.new_state.apps.get_model("experiments", "Tag")
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        # Test that tags were created from projects
        self.assertTrue(Tag.objects.filter(name="Firefox Desktop").exists())
        self.assertTrue(Tag.objects.filter(name="Mobile Performance").exists())
        self.assertTrue(Tag.objects.filter(name="Privacy Features").exists())

        # Test that tags have a color
        desktop_tag = Tag.objects.get(name="Firefox Desktop")
        self.assertTrue(desktop_tag.color)

        mobile_tag = Tag.objects.get(name="Mobile Performance")
        self.assertTrue(mobile_tag.color)

        privacy_tag = Tag.objects.get(name="Privacy Features")
        self.assertTrue(privacy_tag.color)

        # Test that experiments have the correct tags
        experiment1 = NimbusExperiment.objects.get(slug="desktop-feature-test")
        experiment1_tag_names = set(experiment1.tags.values_list("name", flat=True))
        self.assertEqual(experiment1_tag_names, {"Firefox Desktop", "Privacy Features"})

        experiment2 = NimbusExperiment.objects.get(slug="mobile-performance-test")
        experiment2_tag_names = set(experiment2.tags.values_list("name", flat=True))
        self.assertEqual(experiment2_tag_names, {"Mobile Performance"})

        # Test that experiment with no projects has no tags
        experiment3 = NimbusExperiment.objects.get(slug="no-project-experiment")
        self.assertEqual(experiment3.tags.count(), 0)
