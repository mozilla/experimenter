from django.contrib import admin

from experimenter.experiments.models import (
    Experiment,
    ExperimentChangeLog,
    ExperimentVariant,
    NimbusExperiment,
    VariantPreferences
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

    fieldsets = (
        (
            "Overview",
            {
                "fields": (
                    "archived",
                    "type",
                    "owner",
                    "engineering_owner",
                    "status",
                    "subscribers",
                    "related_to",
                    "parent",
                    "projects",
                    "name",
                    "slug",
                    "short_description",
                    "public_description",
                    "proposed_start_date",
                    "proposed_enrollment",
                    "proposed_duration",
                    "bugzilla_id",
                    "recipe_slug",
                    "normandy_id",
                    "other_normandy_ids",
                    "data_science_issue_url",
                    "feature_bugzilla_url",
                    "related_work",
                    "is_paused",
                )
            },
        ),
        (
            "Client Config",
            {
                "fields": (
                    "is_branched_addon",
                    "is_multi_pref",
                    "firefox_channel",
                    "firefox_min_version",
                    "firefox_max_version",
                    "population_percent",
                    "addon_experiment_id",
                    "addon_release_url",
                    "rollout_type",
                    "rollout_playbook",
                    "pref_name",
                    "pref_type",
                    "pref_branch",
                    "design",
                    "locales",
                    "countries",
                    "platforms",
                    "client_matching",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": (
                    "objectives",
                    "analysis_owner",
                    "analysis",
                    "survey_required",
                    "survey_urls",
                    "survey_instructions",
                    "results_url",
                    "results_initial",
                    "results_lessons_learned",
                )
            },
        ),
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
                    "risk_revenue",
                    "risk_data_category",
                    "risk_external_team_impact",
                    "risk_telemetry_data",
                    "risk_ux",
                    "risk_security",
                    "risk_revision",
                    "risk_technical",
                    "risk_technical_description",
                    "risk_higher_risk",
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


class NimbusExperimentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")

    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(ExperimentVariant, ExperimentVariantAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(NimbusExperiment, NimbusExperimentAdmin)
