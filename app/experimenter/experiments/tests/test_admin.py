import mock
from django.conf import settings
from django.urls import reverse
from django.test import TestCase

from experimenter.experiments.admin import ExperimentAdmin
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


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

    def test_returns_200(self):
        user = UserFactory()
        user.is_staff = True
        user.is_superuser = True
        user.save()

        experiment = ExperimentFactory.create_with_status(
            ExperimentFactory.STATUS_DRAFT
        )
        response = self.client.get(
            reverse(
                "admin:experiments_experiment_change",
                kwargs={"object_id": experiment.id},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user.email},
        )
        self.assertEqual(response.status_code, 200)
