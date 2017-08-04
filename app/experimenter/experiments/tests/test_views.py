import json

from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.serializers import ExperimentSerializer
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.projects.tests.factories import ProjectFactory


class TestExperimentListView(TestCase):

    def test_list_view_returns_experiments_for_project(self):
        project = ProjectFactory.create()
        project_experiments = []

        # another projects experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants()

        # started project experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants(
                project=project)
            project_experiments.append(experiment)

        response = self.client.get(
            reverse('experiments-list'), {'project__slug': project.slug})
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            project.experiments.all(), many=True).data

        self.assertEqual(serialized_experiments, json_data)

    def test_list_view_returns_404_for_invalid_project_slug(self):
        response = self.client.get(
            reverse('experiments-list'), {'project__slug': 'bad-slug'})
        self.assertEqual(response.status_code, 404)
