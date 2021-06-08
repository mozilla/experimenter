import datetime
from collections import defaultdict
from statistics import median
from urllib.parse import urljoin

from django.conf import settings
from rest_framework import views
from rest_framework.response import Response

from experimenter.reporting.constants import ReportLogConstants
from experimenter.reporting.models import ReportLog


class ReportDataView(views.APIView):
    def get(self, request, **kwargs):

        start_date = kwargs.get("start_date", None)
        end_date = kwargs.get("end_date", None)
        data = self.get_data(start_date, end_date)
        results = Response(data)
        return results

    def get_data(self, start_date, end_date):

        experiment_names = (
            ReportLog.objects.filter(
                timestamp__range=[start_date, end_date], experiment_new_status="Live"
            )
            .exclude(projects__name__in=ReportLog.EXCLUDED_PROJECTS)
            .values_list("experiment_name", flat=True)
            .distinct()
        )
        reportLogs = ReportLog.objects.filter(experiment_name__in=experiment_names)

        results = []
        project_launch = defaultdict(lambda: 0)
        type_launch = defaultdict(lambda: 0)
        normandy_durations = []
        nimbus_durations = []
        status_durations = defaultdict(lambda: {})

        for name in experiment_names:
            status_duration_times = {}
            experiment_reportlogs = reportLogs.filter(experiment_name=name).order_by(
                "timestamp"
            )
            reportlog = experiment_reportlogs.first()
            type = reportlog.experiment_type
            projects_string = " "
            if projects := reportlog.projects.all():
                projects_string = ", ".join([project.name for project in projects])
                project_launch[projects.first().name] += 1
            type_launch[type] += 1
            pre_live_duration = datetime.timedelta(hours=0)
            url = format_url(reportlog.experiment_slug, type)

            for i in range(len(experiment_reportlogs) - 1):
                current_status = experiment_reportlogs[i].experiment_new_status
                next_status_ts = experiment_reportlogs[i + 1].timestamp
                current_ts = experiment_reportlogs[i].timestamp
                time_delta = next_status_ts - current_ts
                current_time = status_duration_times.get(
                    current_status, datetime.timedelta(hours=0)
                )
                status_duration_times[current_status] = time_delta + current_time
                if current_status != "Live":
                    pre_live_duration += time_delta

            data = {
                "name": name,
                "url": url,
                "type": type,
                "projects": projects_string,
                "time_in_draft": format_time(status_duration_times.get("Draft", None)),
                "time_in_preview": format_time(
                    status_duration_times.get("Preview", None)
                ),
                "time_in_review": format_time(status_duration_times.get("Review", None)),
                "time_in_ship": format_time(status_duration_times.get("Ship", None)),
                "time_in_accepted": format_time(
                    status_duration_times.get("Accepted", None)
                ),
                "time_in_live": format_time(status_duration_times.get("Live", None)),
            }
            results.append(data)

            if "Normandy" in type and "Rollout" not in type:
                normandy_durations.append(pre_live_duration)
            if "Nimbus" in type:
                nimbus_durations.append(pre_live_duration)

            for status, time in status_duration_times.items():
                if status_durations[type].get(status):
                    status_durations[type][status].append(time)
                else:
                    status_durations[type][status] = [time]

        status_medians = {}
        for type in status_durations:
            for status, times in status_durations[type].items():
                if status_medians.get(type):
                    status_medians[type][status] = format_time(median(times))
                else:
                    status_medians[type] = {}
                    status_medians[type][status] = format_time(median(times))

        total_medians = {}
        if normandy_durations or nimbus_durations:
            if normandy_durations:
                total_medians["normandy"] = format_time(median(normandy_durations))
            if nimbus_durations:
                total_medians["nimbus"] = format_time(median(nimbus_durations))
            total_medians["total"] = format_time(
                median(normandy_durations + nimbus_durations)
            )

        response = {
            "headings": ReportLogConstants.REPORT_HEADINGS,
            "data": results,
            "statistics": {
                "status_medians": status_medians,
                "total_medians": total_medians,
                "num_of_launches": type_launch,
                "num_of_launch_by_project": project_launch,
            },
        }

        return response


def format_url(slug, type):
    exp_type = f"experiments/{slug}"
    if "Nimbus" in type:
        exp_type = f"nimbus/{slug}"
    return urljoin("https://{host}/".format(host=settings.HOSTNAME), exp_type)


def format_time(time):
    if time is not None:
        return str(time).replace(",", "")
