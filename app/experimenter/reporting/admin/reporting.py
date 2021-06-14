from django.contrib import admin

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
    list_filter = ("event_reason",)


admin.site.register(ReportLog, ReportLogAdmin)
