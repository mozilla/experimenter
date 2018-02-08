import mock

from django.core.management import call_command
from django.conf import settings
from django.test import TestCase
from stmoab.StatisticalDashboard import StatisticalDashboard

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory


class GenerateDashboardsTest(TestCase):

    def setUp(self):
        self.ORIGINAL_EXTERNAL_API_EXCEPTION = (
            StatisticalDashboard.ExternalAPIError)

        dashboard_patcher = mock.patch((
            'experimenter.experiments.management.commands.'
            'generate_dashboards.StatisticalDashboard'))
        logging_patcher = mock.patch((
            'experimenter.experiments.management.commands.'
            'generate_dashboards.logging'))
        self.mock_logger = logging_patcher.start()
        self.MockExperimentDashboard = dashboard_patcher.start()
        self.MockExperimentDashboard.ExternalAPIError = (
            self.ORIGINAL_EXTERNAL_API_EXCEPTION)
        self.addCleanup(logging_patcher.stop)
        self.addCleanup(dashboard_patcher.stop)

        self.experiment_launched = ExperimentFactory.create_with_status(
            Experiment.STATUS_LAUNCHED)
        self.experiment_complete = ExperimentFactory.create_with_status(
            Experiment.STATUS_COMPLETE)
        self.experiments = [self.experiment_launched, self.experiment_complete]

    def test_dashboard_object_generated(self):
        expected_call_args = [(
            settings.AWS_ACCESS_KEY,
            settings.AWS_SECRET_KEY,
            settings.S3_BUCKET_ID_STATS,
            experiment.project.name,
            experiment.name,
            experiment.slug,
            experiment.start_date.strftime("%Y-%m-%d"),
            (None
                if not experiment.end_date
                else experiment.end_date.strftime("%Y-%m-%d")))
            for experiment in self.experiments]
        expected_public_url = 'www.example.com/some_dashboard_url'

        mock_instance = self.MockExperimentDashboard.return_value
        mock_instance.public_url = expected_public_url

        call_command('generate_dashboards')

        self.assertTrue(self.MockExperimentDashboard.called)
        self.assertEqual(self.MockExperimentDashboard.call_count, 2)

        for idx, call_args in enumerate(
                self.MockExperimentDashboard.call_args_list):
            args, kwargs = call_args
            self.assertEqual(args[0], settings.REDASH_API_KEY)
            self.assertEqual(args[1:], expected_call_args[idx])

        for experiment in self.experiments:
            experiment_obj = Experiment.objects.get(pk=experiment.pk)
            self.assertEqual(experiment_obj.dashboard_url, expected_public_url)

        self.assertEqual(len(
            mock_instance.add_graph_templates.mock_calls), 2)
        self.assertEqual(len(
            mock_instance.add_ttable_data.mock_calls), 2)
        self.assertEqual(len(
            mock_instance.add_ttable.mock_calls), 2)

    def test_external_api_error_is_caught(self):
        ERROR_MESSAGE = 'Unable to communicate with Redash'

        self.MockExperimentDashboard.side_effect = (
            StatisticalDashboard.ExternalAPIError((
                ERROR_MESSAGE)))

        call_command('generate_dashboards')

        self.mock_logger.error.assert_any_call((
          'ExternalAPIError '
          'for {exp}: {err}').format(
          exp=self.experiment_complete, err=ERROR_MESSAGE))

    def test_value_error_is_caught(self):
        ERROR_MESSAGE = 'column_mapping value required'

        self.MockExperimentDashboard.side_effect = (
            ValueError(ERROR_MESSAGE))

        call_command('generate_dashboards')

        self.mock_logger.error.assert_any_call((
          'StatisticalDashboard Value Error '
          'for {exp}: {err}').format(
          exp=self.experiment_complete, err=ERROR_MESSAGE))
