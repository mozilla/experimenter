import json

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    NimbusExperimentFactory,
)
from experimenter.projects.tests.factories import ProjectFactory
from experimenter.reporting.models import ReportLog


@override_settings(HOSTNAME="localhost")
class TestReportDataView(TestCase):
    def test_data_view_returns_correct_data(self):
        timestamp = timezone.now()
        project1 = ProjectFactory.create(name="project1")
        project2 = ProjectFactory.create(name="project2")
        project3 = ProjectFactory.create(name="experiment tools")
        ExperimentFactory.create(name="experiment name", status=Experiment.STATUS_LIVE)

        NimbusExperimentFactory.create(
            name="nimbus name", status=NimbusConstants.Status.LIVE
        )
        for i in range(2):
            for old_status, statuses in Experiment.STATUS_TRANSITIONS.items():
                if len(statuses):
                    reportlog = ReportLog.objects.create(
                        timestamp=timestamp,
                        experiment_slug=f"experiment-name-{i}",
                        experiment_name=f"experiment name {i}",
                        experiment_type=ReportLog.ExperimentType.NORMANDY_PREF,
                        experiment_old_status=old_status,
                        experiment_new_status=statuses[-1],
                        event=ReportLog.Event.UPDATE,
                        event_reason=ReportLog.EventReason.STATUS_CHANGE,
                        comment="",
                    )
                    reportlog.projects.set([project1, project2])
                    timestamp += timezone.timedelta(hours=1)

        nimbus_status_order = [
            NimbusConstants.Status.DRAFT,
            NimbusConstants.Status.PREVIEW,
            NimbusConstants.Status.DRAFT,
            NimbusConstants.Status.LIVE,
            NimbusConstants.Status.COMPLETE,
        ]

        for i in range(len(nimbus_status_order) - 1):
            ReportLog.objects.create(
                timestamp=timestamp,
                experiment_slug="nimbus-name",
                experiment_name="nimbus name",
                experiment_type=ReportLog.ExperimentType.NIMBUS_DESKTOP,
                experiment_old_status=nimbus_status_order[i],
                experiment_new_status=nimbus_status_order[i + 1],
                event=ReportLog.Event.UPDATE,
                event_reason=ReportLog.EventReason.STATUS_CHANGE,
                comment="",
            )
            timestamp += timezone.timedelta(hours=2)

            # test related rollout report log that will be excluded in calculations
            reportlog3 = ReportLog.objects.create(
                timestamp=timezone.now(),
                experiment_slug="experiment name 3",
                experiment_name="experiment name 3",
                experiment_type=ReportLog.ExperimentType.NORMANDY_ROLLOUT,
                experiment_old_status=Experiment.STATUS_ACCEPTED,
                experiment_new_status=Experiment.STATUS_LIVE,
                event=ReportLog.Event.UPDATE,
                event_reason=ReportLog.EventReason.LAUNCH,
                comment="",
            )
            reportlog3.projects.set([project3])

        start_date = timezone.now() - timezone.timedelta(days=2)
        start_date_str = timezone.datetime.strftime(start_date, "%Y-%m-%d")
        end_date = timezone.now() + timezone.timedelta(days=2)
        end_date_str = timezone.datetime.strftime(end_date, "%Y-%m-%d")

        response = self.client.get(
            reverse(
                "reporting-rest",
                kwargs={"start_date": start_date_str, "end_date": end_date_str},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.maxDiff = None

        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        expected_data = {
            "data": [
                {
                    "name": "nimbus name",
                    "projects": " ",
                    "time_in_accepted": None,
                    "time_in_draft": "2:00:00",
                    "time_in_live": "2:00:00",
                    "time_in_preview": "2:00:00",
                    "time_in_review": None,
                    "time_in_ship": None,
                    "type": "Nimbus-Firefox-Desktop",
                    "url": "https://localhost/nimbus/nimbus-name",
                },
                {
                    "name": "experiment name 0",
                    "projects": "project1, project2",
                    "time_in_accepted": "1:00:00",
                    "time_in_draft": None,
                    "time_in_live": "1:00:00",
                    "time_in_preview": None,
                    "time_in_review": "1:00:00",
                    "time_in_ship": "1:00:00",
                    "type": "Normandy-Pref",
                    "url": "https://localhost/experiments/experiment-name-0",
                },
                {
                    "name": "experiment name 1",
                    "projects": "project1, project2",
                    "time_in_accepted": "1:00:00",
                    "time_in_draft": None,
                    "time_in_live": "1:00:00",
                    "time_in_preview": None,
                    "time_in_review": "1:00:00",
                    "time_in_ship": "1:00:00",
                    "type": "Normandy-Pref",
                    "url": "https://localhost/experiments/experiment-name-1",
                },
            ],
            "headings": [
                "name",
                "url",
                "type",
                "projects",
                "time_in_draft",
                "time_in_preview",
                "time_in_review",
                "time_in_ship",
                "time_in_accepted",
                "time_in_live",
            ],
            "statistics": {
                "num_of_launch_by_project": {"project1": 2},
                "num_of_launches": {"Nimbus-Firefox-Desktop": 1, "Normandy-Pref": 2},
                "status_medians": {
                    "Nimbus-Firefox-Desktop": {
                        "Draft": "2:00:00",
                        "Live": "2:00:00",
                        "Preview": "2:00:00",
                    },
                    "Normandy-Pref": {
                        "Accepted": "1:00:00",
                        "Live": "1:00:00",
                        "Review": "1:00:00",
                        "Ship": "1:00:00",
                    },
                },
                "total_medians": {
                    "nimbus": "4:00:00",
                    "normandy": "3:00:00",
                    "total": "3:00:00",
                },
            },
        }

        for data in expected_data["data"]:
            self.assertIn(data, json_data["data"])
        self.assertEqual(json_data["headings"], expected_data["headings"])
        self.assertEqual(json_data["statistics"], expected_data["statistics"])
