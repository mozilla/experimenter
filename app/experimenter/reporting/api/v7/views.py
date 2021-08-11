from collections import defaultdict
from statistics import median
from urllib.parse import urljoin

from django.conf import settings
from django.utils import timezone
from rest_framework import views
from rest_framework.response import Response

from experimenter.reporting.constants import ReportLogConstants
from experimenter.reporting.models import ReportLog


class ReportDataView(views.APIView):
    def get(self, request, **kwargs):

        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        data = self.get_data(start_date, end_date)
        results = Response(data)
        return results

    def get_data(self, start_date, end_date):

        experiment_names = (
            ReportLog.objects.filter(
                timestamp__range=[start_date, end_date],
                experiment_new_status=ReportLog.ExperimentStatus.LIVE,
            )
            .exclude(projects__name__in=ReportLog.EXCLUDED_PROJECTS)
            .values_list("experiment_slug", flat=True)
            .distinct()
        )
        report_logs = ReportLog.objects.filter(experiment_slug__in=experiment_names)

        results = []
        project_launch = defaultdict(lambda: 0)
        type_launch = defaultdict(lambda: 0)
        normandy_durations = []
        nimbus_durations = []
        status_durations = defaultdict(lambda: {})

        for slug in experiment_names:
            status_duration_times = {}
            experiment_reportlogs = report_logs.filter(experiment_slug=slug).order_by(
                "timestamp"
            )
            report_log = experiment_reportlogs.first()
            experiment_type = report_log.experiment_type
            projects_string = " "
            if projects := report_log.projects.all():
                projects_string = ", ".join([project.name for project in projects])
                project_launch[projects.first().name] += 1
            type_launch[experiment_type] += 1

            pre_live_duration = compute_duration_time(
                experiment_reportlogs, status_duration_times
            )

            construct_results_data(
                report_log, projects_string, results, status_duration_times
            )

            compute_durations(
                report_log,
                nimbus_durations,
                normandy_durations,
                pre_live_duration,
                status_duration_times,
                status_durations,
            )

        status_medians = compute_status_medians(status_durations)

        total_medians = compute_total_medians(nimbus_durations, normandy_durations)

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


def compute_total_medians(nimbus_durations, normandy_durations):
    total_medians = {}
    if normandy_durations or nimbus_durations:
        if normandy_durations:
            total_medians["normandy"] = format_time(median(normandy_durations))
        if nimbus_durations:
            total_medians["nimbus"] = format_time(median(nimbus_durations))
        total_medians["total"] = format_time(
            median(normandy_durations + nimbus_durations)
        )
    return total_medians


def compute_status_medians(status_durations):
    status_medians = {}
    for experiment_type in status_durations:
        for status, times in status_durations[experiment_type].items():
            if status_medians.get(experiment_type):
                status_medians[experiment_type][status] = format_time(median(times))
            else:
                status_medians[experiment_type] = {}
                status_medians[experiment_type][status] = format_time(median(times))
    return status_medians


def compute_durations(
    report_log,
    nimbus_durations,
    normandy_durations,
    pre_live_duration,
    status_duration_times,
    status_durations,
):
    experiment_type = report_log.experiment_type
    if report_log.is_normandy_experiment_type:
        normandy_durations.append(pre_live_duration)
    if report_log.is_nimbus_type:
        nimbus_durations.append(pre_live_duration)
    for status, time in status_duration_times.items():
        if status_durations[experiment_type].get(status):
            status_durations[experiment_type][status].append(time)
        else:
            status_durations[experiment_type][status] = [time]


def construct_results_data(reportlog, projects_string, results, status_duration_times):
    data = {
        "name": reportlog.experiment_name,
        "url": format_url(reportlog),
        "type": reportlog.experiment_type,
        "projects": projects_string,
        "time_in_draft": format_time(
            status_duration_times.get(ReportLog.ExperimentStatus.DRAFT)
        ),
        "time_in_preview": format_time(
            status_duration_times.get(ReportLog.ExperimentStatus.PREVIEW)
        ),
        "time_in_review": format_time(
            status_duration_times.get(ReportLog.ExperimentStatus.REVIEW)
        ),
        "time_in_ship": format_time(
            status_duration_times.get(ReportLog.ExperimentStatus.SHIP)
        ),
        "time_in_accepted": format_time(
            status_duration_times.get(ReportLog.ExperimentStatus.ACCEPTED)
        ),
        "time_in_live": format_time(
            status_duration_times.get(ReportLog.ExperimentStatus.LIVE)
        ),
    }
    results.append(data)


def compute_duration_time(experiment_reportlogs, status_duration_times):
    pre_live_duration = timezone.timedelta(hours=0)
    for i in range(len(experiment_reportlogs) - 1):
        current_status = experiment_reportlogs[i].experiment_new_status
        next_status_ts = experiment_reportlogs[i + 1].timestamp
        current_ts = experiment_reportlogs[i].timestamp
        time_delta = next_status_ts - current_ts
        current_time = status_duration_times.get(
            current_status, timezone.timedelta(hours=0)
        )
        status_duration_times[current_status] = time_delta + current_time
        if current_status != ReportLog.ExperimentStatus.LIVE:
            pre_live_duration += time_delta
    return pre_live_duration


def format_url(report_log):
    slug = report_log.experiment_slug
    exp_type = urljoin("experiments/", slug)
    if report_log.is_nimbus_type:
        exp_type = urljoin("nimbus/", slug)
    return urljoin("https://{host}/".format(host=settings.HOSTNAME), exp_type)


def format_time(time):
    if time is not None:
        return str(time).replace(",", "")
