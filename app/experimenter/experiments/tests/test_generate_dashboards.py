import mock

from django.core.management import call_command
from django.test import TestCase

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory

from redash_client.client import RedashClient


class GenerateDashboardsTest(TestCase):

    def setUp(self):
        dashboard_patcher = mock.patch((
            'experimenter.experiments.management.commands.'
            'generate_dashboards.ActivityStreamExperimentDashboard'))
        logging_patcher = mock.patch((
            'experimenter.experiments.management.commands.'
            'generate_dashboards.logging'))
        self.mock_logger = logging_patcher.start()
        self.MockExperimentDashboard = dashboard_patcher.start()
        self.addCleanup(logging_patcher.stop)
        self.addCleanup(dashboard_patcher.stop)

        self.experiment = ExperimentFactory.create_with_variants()

        # Move our experiment into "launched" phase so that we create
        # dashboards for it.
        self.experiment.status = self.experiment.STATUS_PENDING
        self.experiment.save()
        self.experiment.status = self.experiment.STATUS_ACCEPTED
        self.experiment.save()
        self.experiment.status = self.experiment.STATUS_LAUNCHED
        self.experiment.save()

    def test_dashboard_object_generated(self):
        expected_call_args = (
            self.experiment.project.name,
            self.experiment.name,
            self.experiment.slug)
        expected_public_url = "www.some_dashboard_url.com"

        mock_instance = self.MockExperimentDashboard.return_value
        mock_instance.public_url = expected_public_url

        call_command('generate_dashboards')
        args, kwargs = self.MockExperimentDashboard.call_args

        self.assertTrue(self.MockExperimentDashboard.called)
        self.assertTrue(isinstance(args[0], RedashClient))
        self.assertEqual(args[1:], expected_call_args)

        experiment = Experiment.objects.get(pk=self.experiment.pk)
        self.assertEqual(experiment.dashboard_url, expected_public_url)

        self.assertEqual(len(
            mock_instance.add_graph_templates.mock_calls), 2)

    def test_redash_client_error_is_caught(self):
        self.MockExperimentDashboard.side_effect = (
            RedashClient.RedashClientException)

        call_command('generate_dashboards')

        self.mock_logger.error.assert_called_with((
          "Unable to generate dashboard "
          "for {exp}").format(exp=self.experiment))
