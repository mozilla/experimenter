from django.contrib import admin

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
    list_display = (
        "name",
        "type",
        "status",
        "owner",
        "firefox_version",
        "firefox_channel",
    )
    list_filter = ("status", "firefox_version", "firefox_channel")

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
                    "normandy_slug",
                    "normandy_id",
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
                    "firefox_version",
                    "population_percent",
                    "addon_name",
                    "addon_experiment_id",
                    "addon_testing_url",
                    "addon_release_url",
                    "pref_key",
                    "pref_type",
                    "pref_branch",
                    "locales",
                    "countries",
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
    )

    prepopulated_fields = {"slug": ("name",)}

    def get_actions(self, request):
        return []

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Experiment, ExperimentAdmin)
