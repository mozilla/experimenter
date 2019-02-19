from django.contrib import admin
from django.utils.html import format_html

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
)


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
    )


class ExperimentAdmin(admin.ModelAdmin):
    inlines = (ExperimentVariantInlineAdmin, ExperimentChangeLogInlineAdmin)
    list_display = ("name", "type", "status")

    fieldsets = (
        (
            "Overview",
            {
                "fields": (
                    "archived",
                    "type",
                    "owner",
                    "project",
                    "status",
                    "name",
                    "slug",
                    "short_description",
                    "proposed_start_date",
                    "proposed_enrollment",
                    "proposed_duration",
                    "bugzilla_id",
                    "data_science_bugzilla_url",
                    "feature_bugzilla_url",
                    "related_work",
                )
            },
        ),
        (
            "Client Config",
            {
                "fields": (
                    "firefox_channel",
                    "firefox_min_version",
                    "population_percent",
                    "pref_key",
                    "pref_type",
                    "pref_branch",
                    "client_matching",
                )
            },
        ),
        ("Notes", {"fields": ("objectives", "analysis_owner", "analysis")}),
        (
            "Reviews",
            {
                "fields": (
                    "review_science",
                    "review_engineering",
                    "review_qa_requested",
                    "review_intent_to_ship",
                    "review_bugzilla",
                    "review_qa",
                    "review_relman",
                    "review_advisory",
                    "review_legal",
                    "review_ux",
                    "review_security",
                    "review_vp",
                    "review_data_steward",
                    "review_comms",
                    "review_impacted_teams",
                )
            },
        ),
        (
            "Risks & Testing",
            {
                "fields": (
                    "risk_partner_related",
                    "risk_brand",
                    "risk_fast_shipped",
                    "risk_confidential",
                    "risk_release_population",
                    "risk_technical",
                    "risk_technical_description",
                    "risks",
                    "testing",
                    "test_builds",
                    "qa_status",
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
        url = obj.dashboard_url
        return format_html(
            f'<a href="{url}" target="_blank" rel="noreferrer noopener"'
            f'>{url}</a>'
        )

    show_dashboard_url.short_description = "Dashboard URL"


admin.site.register(Experiment, ExperimentAdmin)
