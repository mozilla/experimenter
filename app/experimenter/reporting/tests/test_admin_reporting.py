from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.base.tests.mixins import MockRequestMixin
from experimenter.openidc.tests.factories import UserFactory
from experimenter.reporting.tests.factories import ReportLogFactory


class ReportLogAdminTest(MockRequestMixin, TestCase):
    def test_returns_200(self):
        user = UserFactory()
        user.is_staff = True
        user.is_superuser = True
        user.save()

        reportLog = ReportLogFactory.create()
        response = self.client.get(
            reverse(
                "admin:reporting_reportlog_change", kwargs={"object_id": reportLog.id}
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user.email},
        )
        self.assertEqual(response.status_code, 200)
