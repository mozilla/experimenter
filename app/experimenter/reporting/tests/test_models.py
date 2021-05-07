from django.core.exceptions import ValidationError
from django.test import TestCase

from experimenter.reporting.models import ReportLog
from experimenter.reporting.tests.factories import ReportLogFactory


class TestReportLog(TestCase):
    def test_reportlog_with_bad_event_pair(self):
        self.assertRaises(
            ValidationError, ReportLogFactory.create, event="Update", event_reason="Clone"
        )

    def test_reportlog_saves_correctly(self):
        self.assertEqual(ReportLog.objects.count(), 0)
        ReportLogFactory.create()
        self.assertEqual(ReportLog.objects.count(), 1)

    def test_reportlog_saves_with_null_old_status(self):
        self.assertEqual(ReportLog.objects.count(), 0)
        ReportLog.objects.create(
            experiment_slug="experiment-slug",
            experiment_name="experiment name",
            experiment_type="Nimbus IOS",
            experiment_new_status="Draft",
            event="Create",
            event_reason="New",
        )
        self.assertEqual(ReportLog.objects.count(), 1)
