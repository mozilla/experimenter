import csv

from django.contrib import admin
from django.http import HttpResponse

from experimenter.reporting.models import ReportLog


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

    def has_delete_permission(self, request, obj=None):
        return False


def download_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment;" "filename=reportlog.csv"
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


admin.site.add_action(download_csv, "download_csv")
admin.site.register(ReportLog, ReportLogAdmin)
