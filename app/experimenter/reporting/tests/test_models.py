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
