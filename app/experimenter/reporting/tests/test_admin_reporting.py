from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.base.tests.mixins import MockRequestMixin
from experimenter.openidc.tests.factories import UserFactory
from experimenter.reporting.admin.reporting import (
    CPRReportListFilter,
    ReportLogAdmin,
    download_csv,
)
from experimenter.reporting.constants import ReportLogConstants
from experimenter.reporting.models import ReportLog
from experimenter.reporting.tests.factories import ReportLogFactory


class ReportLogAdminTest(MockRequestMixin, TestCase):
    def test_download_csv(self):
        report_log = ReportLogFactory.create()
        response = download_csv(ReportLogAdmin, self.request, ReportLog.objects.all())
        self.assertIn(str(report_log.timestamp), str(response.content))
        self.assertEqual(response.status_code, 200)

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


class CPRReportListFilterTest(TestCase):
    def setUp(self):
        self.report_log1 = ReportLogFactory.create(
            experiment_type=ReportLogConstants.ExperimentType.NORMANDY_PREF,
            experiment_old_status=ReportLogConstants.ExperimentStatus.ACCEPTED,
            experiment_new_status=ReportLogConstants.ExperimentStatus.ACCEPTED,
        )
        self.report_log2 = ReportLogFactory.create(
            experiment_type=ReportLogConstants.ExperimentType.NORMANDY_ADDON,
            experiment_old_status=ReportLogConstants.ExperimentStatus.ACCEPTED,
            experiment_new_status=ReportLogConstants.ExperimentStatus.LIVE,
        )
        self.report_log3 = ReportLogFactory.create(
            experiment_type=ReportLogConstants.ExperimentType.NORMANDY_ROLLOUT,
            experiment_old_status=ReportLogConstants.ExperimentStatus.LIVE,
            experiment_new_status=ReportLogConstants.ExperimentStatus.LIVE,
        )
        self.report_log4 = ReportLogFactory.create(
            experiment_type=ReportLogConstants.ExperimentType.NORMANDY_ROLLOUT,
            experiment_old_status=ReportLogConstants.ExperimentStatus.LIVE,
            experiment_new_status=ReportLogConstants.ExperimentStatus.COMPLETE,
        )

    def test_cpr_filtering_filters_normandy_updates_only(self):

        filter = CPRReportListFilter(
            None, {"CPR ReportLogs": "cpr"}, ReportLog, ReportLogAdmin
        )
        query_result = filter.queryset(None, ReportLog.objects.all())
        self.assertEqual(
            set([self.report_log1, self.report_log2, self.report_log3, self.report_log4]),
            set(list(query_result)),
        )

    def test_no_filtering_includes_all(self):
        ReportLogFactory.create(
            experiment_type=ReportLogConstants.ExperimentType.NORMANDY_ROLLOUT,
            experiment_old_status=None,
            experiment_new_status=ReportLogConstants.ExperimentStatus.DRAFT,
        )
        ReportLogFactory.create(
            experiment_type=ReportLogConstants.ExperimentType.NIMBUS_IOS
        )
        ReportLogFactory.create(
            experiment_type=ReportLogConstants.ExperimentType.NIMBUS_DESKTOP,
            experiment_old_status=ReportLogConstants.ExperimentStatus.LIVE,
            experiment_new_status=ReportLogConstants.ExperimentStatus.LIVE,
        )
        filter = CPRReportListFilter(
            None, {"CPR ReportLogs": "all"}, ReportLog, ReportLogAdmin
        )
        query_result = filter.queryset(None, ReportLog.objects.all())
        self.assertEqual(query_result.count(), 7)
