import json

from django.test import TestCase
from django.urls import reverse

from experimenter.projects.tests.factories import ProjectFactory
from experimenter.experiments.tests.factories import ExperimentFactory


class TestExperimentListView(TestCase):

    def test_list_view_returns_started_experiments_for_project(self):
        project = ProjectFactory.create()
        started_experiments = []

        # unstarted experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants()

        # another projects experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants(project=project)

        # started experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants(
                project=project)
            experiment.status = experiment.EXPERIMENT_STARTED
            experiment.save()
            started_experiments.append(experiment)

        # completed experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants(
                project=project)
            experiment.status = experiment.EXPERIMENT_STARTED
            experiment.save()

            experiment.status = experiment.EXPERIMENT_COMPLETE
            experiment.save()

            started_experiments.append(experiment)

        # invalid experiments should be included
        experiment = ExperimentFactory.create_with_variants(
            project=project)
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        experiment.status = experiment.EXPERIMENT_INVALID
        experiment.save()

        started_experiments.append(experiment)

        # rejected experiments should be included
        experiment = ExperimentFactory.create_with_variants(
            project=project)
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        experiment.status = experiment.EXPERIMENT_REJECTED
        experiment.save()

        started_experiments.append(experiment)

        response = self.client.get(
            reverse('experiments-list', kwargs={'project_slug': project.slug}))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        self.assertEqual(len(json_data), len(started_experiments))

        self.assertEqual(
            set(exp_data['slug'] for exp_data in json_data),
            set(exp.slug for exp in started_experiments),
        )

    def test_list_view_returns_404_for_invalid_project_slug(self):
        response = self.client.get(
            reverse('experiments-list', kwargs={'project_slug': 'bad slug'}))
        self.assertEqual(response.status_code, 404)
