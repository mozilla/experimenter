from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentDocumentationLinkMixin(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_update_links(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        data = {
            "changelog_message": "test changelog message",
            "public_description": "changed",
            "documentation_links": [
                {
                    "title": NimbusExperiment.DocumentationLink.DS_JIRA,
                    "link": "https://example.com/1",
                },
                {
                    "title": NimbusExperiment.DocumentationLink.ENG_TICKET,
                    "link": "https://example.com/2",
                },
            ],
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assert_documentation_links(experiment.id, data["documentation_links"])

    def test_serializer_preserves_links_when_absent_in_data(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        links_before = []
        for link in experiment.documentation_links.all():
            links_before.append(
                {
                    "title": link.title,
                    "link": link.link,
                }
            )
        data = {
            "public_description": "changed",
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assert_documentation_links(experiment.id, links_before)

    def test_serializer_preserves_links_with_branch_update(self):
        """
        Reproduction for EXP-1788: branch update deleted documentation
        links. Topically more appropriate for the branch serializer suite,
        but the links assert method lives here
        """
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        links_before = []
        for link in experiment.documentation_links.all():
            links_before.append(
                {
                    "title": link.title,
                    "link": link.link,
                }
            )
        data = {
            "public_description": "changed reference",
            "reference_branch": {
                "description": "changed",
                "feature_enabled": False,
                "name": "also changed reference",
                "ratio": 1,
            },
            "treatment_branches": [
                {
                    "description": "changed treatment",
                    "feature_enabled": False,
                    "name": "also changed treatment",
                    "ratio": 1,
                },
            ],
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assert_documentation_links(experiment.id, links_before)

    def test_serializer_supports_multiple_links_of_same_type(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        data = {
            "changelog_message": "test changelog message",
            "public_description": "changed",
            "documentation_links": [
                {
                    "title": NimbusExperiment.DocumentationLink.ENG_TICKET,
                    "link": "https://example.com/1",
                },
                {
                    "title": NimbusExperiment.DocumentationLink.ENG_TICKET,
                    "link": "https://example.com/2",
                },
            ],
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assert_documentation_links(experiment.id, data["documentation_links"])

    def assert_documentation_links(self, experiment_id, links_data):
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        documentation_links = experiment.documentation_links.all()
        for key in (
            "title",
            "link",
        ):
            self.assertEqual(
                {b[key] for b in links_data},
                {getattr(b, key) for b in documentation_links},
            )
