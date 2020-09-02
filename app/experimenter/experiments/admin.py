from django.contrib import admin

from experimenter.experiments.models import (
    Experiment,
    ExperimentCore,
    ExperimentRapid,
    ExperimentVariant,
    ExperimentChangeLog,
    VariantPreferences,
)
from experimenter.projects.models import Project


class ExperimentVariantInlineAdmin(admin.StackedInline):
    extra = 0
    fields = ("is_control", "name", "slug", "ratio", "description", "value")
    model = ExperimentVariant
    prepopulated_fields = {"slug": ("name",)}
    verbose_name = "Experiment Variant"
    verbose_name_plural = "Experiment Variants"


class ExperimentChangeLogInlineAdmin(admin.TabularInline):
    extra = 1
    model = ExperimentChangeLog

    fields = (
        "changed_by",
        "changed_on",
        "old_status",
        "new_status",
        "message",
        "changed_values",
    )


class ExperimentAdmin(admin.ModelAdmin):
    inlines = (ExperimentVariantInlineAdmin, ExperimentChangeLogInlineAdmin)
    list_display = (
        "name",
        "type",
        "status",
        "owner",
        "firefox_min_version",
        "firefox_max_version",
        "firefox_channel",
    )
    list_filter = ("status", "firefox_channel")

    prepopulated_fields = {"slug": ("name",)}

    def get_actions(self, request):
        return []

    def has_delete_permission(self, request, obj=None):
        return False


class ExperimentVariantPreferenceInlineAdmin(admin.StackedInline):
    extra = 0
    fields = ("pref_name", "pref_type", "pref_branch", "pref_value")
    model = VariantPreferences
    verbose_name = "Experiment Variant Preference"
    verbose_name_plural = "Experiment Variants Preferences"


class ExperimentVariantAdmin(admin.ModelAdmin):
    inlines = (ExperimentVariantPreferenceInlineAdmin,)
    list_display = ("name", "experiment", "ratio", "value")


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")

    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(ExperimentVariant, ExperimentVariantAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ExperimentCore)
admin.site.register(ExperimentRapid)
