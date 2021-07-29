import csv

from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse
from rangefilter.filters import DateTimeRangeFilter

from experimenter.reporting.models import ReportLog


def download_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=reportlog.csv"
    writer = csv.writer(response)
    writer.writerow(
        [
            "Timestamp",
            "Experiment Slug",
            "Experiment Name",
            "Experiment Type",
            "Old Status",
            "New Status",
            "Event",
            "Event Reason",
            "Comment",
            "Projects",
        ]
    )

    for rl in queryset:
        projects = list(rl.projects.values_list("name", flat=True).order_by("name"))
        writer.writerow(
            [
                rl.timestamp,
                rl.experiment_slug,
                rl.experiment_name,
                rl.experiment_type,
                rl.experiment_old_status,
                rl.experiment_new_status,
                rl.event,
                rl.event_reason,
                rl.comment,
                projects,
            ]
        )

    return response


class CPRReportListFilter(admin.SimpleListFilter):
    title = "Normandy Launch Update Report Log Filter"
    parameter_name = "Normandy Launch Update ReportLogs"

    def lookups(self, request, model_admin):
        return [("Normandy Launch Updates", "Normandy Launch Updates Only")]

    def queryset(self, request, queryset):
        if self.value() == "Normandy Launch Updates":
            return queryset.filter(
                Q(experiment_type__startswith="Normandy")
                & Q(
                    Q(
                        experiment_old_status=ReportLog.ExperimentStatus.ACCEPTED,
                        experiment_new_status=ReportLog.ExperimentStatus.ACCEPTED,
                    )
                    | Q(
                        experiment_old_status=ReportLog.ExperimentStatus.ACCEPTED,
                        experiment_new_status=ReportLog.ExperimentStatus.LIVE,
                    )
                    | Q(
                        experiment_old_status=ReportLog.ExperimentStatus.LIVE,
                        experiment_new_status=ReportLog.ExperimentStatus.LIVE,
                    )
                    | Q(
                        experiment_old_status=ReportLog.ExperimentStatus.LIVE,
                        experiment_new_status=ReportLog.ExperimentStatus.COMPLETE,
                    )
                )
            )
        return queryset


class ReportLogAdmin(admin.ModelAdmin):
    field_sets = (
        "timestamp",
        "experiment_slug",
        "experiment_name",
        "experiment_type",
        "experiment_old_status",
        "experiment_new_status",
        "event",
        "event_reason",
        "comment",
        "projects",
    )
    list_filter = (
        ("timestamp", DateTimeRangeFilter),
        "event_reason",
        CPRReportListFilter,
    )

    actions = [download_csv]


admin.site.register(ReportLog, ReportLogAdmin)
