import mock
from django.test import TestCase


from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.admin import ExperimentAdmin


class ExperimentAdminTest(TestCase):

    def test_no_actions(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        self.assertEqual(experiment_admin.get_actions(mock.Mock()), [])

    def test_no_delete_permission(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        self.assertFalse(experiment_admin.has_delete_permission(mock.Mock()))

    def test_show_dashboard_url_returns_link(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        experiment = ExperimentFactory.create_with_variants()
        self.assertEqual(
            experiment_admin.show_dashboard_url(experiment),
            '<a href="{url}" target="_blank">{url}</a>'.format(
                url=experiment.dashboard_url
            ),
        )
