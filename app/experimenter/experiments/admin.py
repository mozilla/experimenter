from django import forms
from django.contrib import admin
from django.utils.html import format_html

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
)


class BaseVariantInlineAdmin(admin.StackedInline):
    max_num = 1
    model = ExperimentVariant
    prepopulated_fields = {"slug": ("name",)}

    def has_delete_permission(self, request, obj=None):
        return False


class ControlVariantModelForm(forms.ModelForm):

    def save(self, commit=True):
        self.instance.is_control = True
        return super().save(commit=commit)

    class Meta:
        model = ExperimentVariant
        exclude = []


class ControlVariantInlineAdmin(BaseVariantInlineAdmin):
    fields = ("name", "slug", "ratio", "description", "value")
    form = ControlVariantModelForm
    verbose_name = "Control Variant"
    verbose_name_plural = "Control Variant"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=True)


class ExperimentVariantInlineAdmin(BaseVariantInlineAdmin):
    fields = ("name", "slug", "ratio", "description", "value")
    verbose_name = "Experiment Variant"
    verbose_name_plural = "Experiment Variant"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=False)


class ExperimentChangeLogInlineAdmin(admin.TabularInline):
    extra = 1
    model = ExperimentChangeLog

    fields = (
        "changed_by",
        "changed_on",
        "old_status",
        "new_status",
        "message",
    )


class ExperimentAdmin(admin.ModelAdmin):
    inlines = (
        ControlVariantInlineAdmin,
        ExperimentVariantInlineAdmin,
        ExperimentChangeLogInlineAdmin,
    )
    list_display = ("name", "project", "status")

    fieldsets = (
        (
            "Overview",
            {
                "fields": (
                    "archived",
                    "owner",
                    "project",
                    "status",
                    "name",
                    "slug",
                    "short_description",
                    "proposed_start_date",
                    "proposed_end_date",
                )
            },
        ),
        (
            "Client Config",
            {
                "fields": (
                    "pref_key",
                    "pref_type",
                    "pref_branch",
                    "firefox_channel",
                    "firefox_version",
                    "population_percent",
                    "client_matching",
                )
            },
        ),
        ("Notes", {"fields": ("objectives", "analysis")}),
        (
            "Risks & Testing",
            {
                "fields": (
                    "risk_partner_related",
                    "risk_brand",
                    "risk_fast_shipped",
                    "risk_confidential",
                    "risk_release_population",
                    "risks",
                    "testing",
                )
            },
        ),
        (
            "Telemetry",
            {
                "fields": (
                    "dashboard_url",
                    "dashboard_image_url",
                    "enrollment_dashboard_url",
                    "total_users",
                )
            },
        ),
    )

    prepopulated_fields = {"slug": ("name",)}

    def get_actions(self, request):
        return []

    def has_delete_permission(self, request, obj=None):
        return False

    def show_dashboard_url(self, obj):
        return format_html(
            '<a href="{url}" target="_blank">{url}</a>'.format(
                url=obj.dashboard_url
            )
        )

    show_dashboard_url.short_description = "Dashboard URL"


admin.site.register(Experiment, ExperimentAdmin)
