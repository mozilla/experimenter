import time
from rest_framework import serializers


from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
    VariantPreferences,
)
from experimenter.projects.models import Project
from experimenter.experiments.serializers.geo import CountrySerializer, LocaleSerializer


class JSTimestampField(serializers.Field):
    """
    Serialize a datetime object into javascript timestamp
    ie unix time in ms
    """

    def to_representation(self, obj):
        if obj:
            return time.mktime(obj.timetuple()) * 1000
        else:
            return None


class PrefTypeField(serializers.Field):
    def to_representation(self, obj):
        if obj == Experiment.PREF_TYPE_JSON_STR:
            return Experiment.PREF_TYPE_STR
        else:
            return obj


class ExperimentPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantPreferences
        fields = ("pref_name", "pref_type", "pref_branch", "pref_value")


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("slug",)


class ExperimentVariantSerializer(serializers.ModelSerializer):
    preferences = ExperimentPreferenceSerializer(many=True, required=False)

    class Meta:
        model = ExperimentVariant
        fields = (
            "description",
            "is_control",
            "name",
            "ratio",
            "slug",
            "value",
            "addon_release_url",
            "preferences",
        )


class ChangeLogSerializer(serializers.ModelSerializer):
    variants = ExperimentVariantSerializer(many=True, required=False)
    locales = LocaleSerializer(many=True, required=False)
    countries = CountrySerializer(many=True, required=False)
    projects = ProjectSerializer(many=True, required=False)

    class Meta:
        model = Experiment
        fields = (
            "type",
            "owner",
            "name",
            "short_description",
            "related_work",
            "related_to",
            "proposed_start_date",
            "proposed_duration",
            "proposed_enrollment",
            "design",
            "addon_experiment_id",
            "addon_release_url",
            "pref_name",
            "pref_type",
            "pref_branch",
            "public_name",
            "public_description",
            "population_percent",
            "firefox_min_version",
            "firefox_max_version",
            "firefox_channel",
            "client_matching",
            "locales",
            "countries",
            "projects",
            "platform",
            "objectives",
            "analysis",
            "analysis_owner",
            "survey_required",
            "survey_urls",
            "survey_instructions",
            "engineering_owner",
            "bugzilla_id",
            "normandy_slug",
            "normandy_id",
            "data_science_issue_url",
            "feature_bugzilla_url",
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
            "risks",
            "testing",
            "test_builds",
            "qa_status",
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
            "variants",
            "results_url",
            "results_initial",
            "results_lessons_learned",
            "results_fail_to_launch",
            "results_recipe_errors",
            "results_restarts",
            "results_low_enrollment",
            "results_early_end",
            "results_no_usable_data",
            "results_failures_notes",
            "results_changes_to_firefox",
            "results_data_for_hypothesis",
            "results_confidence",
            "results_measure_impact",
            "results_impact_notes",
            "rollout_type",
            "rollout_playbook",
        )


class ExperimentChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentChangeLog
        fields = ("changed_on", "pretty_status", "new_status", "old_status")


class ResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = (
            "results_url",
            "results_initial",
            "results_lessons_learned",
            "results_fail_to_launch",
            "results_recipe_errors",
            "results_restarts",
            "results_low_enrollment",
            "results_early_end",
            "results_no_usable_data",
            "results_failures_notes",
            "results_changes_to_firefox",
            "results_data_for_hypothesis",
            "results_confidence",
            "results_measure_impact",
            "results_impact_notes",
        )


class ExperimentSerializer(serializers.ModelSerializer):
    start_date = JSTimestampField()
    end_date = JSTimestampField()
    proposed_start_date = JSTimestampField()
    variants = ExperimentVariantSerializer(many=True)
    locales = LocaleSerializer(many=True)
    countries = CountrySerializer(many=True)
    pref_type = PrefTypeField()
    changes = ExperimentChangeLogSerializer(many=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = (
            "experiment_url",
            "type",
            "name",
            "slug",
            "public_name",
            "public_description",
            "status",
            "client_matching",
            "locales",
            "countries",
            "platform",
            "start_date",
            "end_date",
            "population",
            "population_percent",
            "firefox_channel",
            "firefox_min_version",
            "firefox_max_version",
            "addon_experiment_id",
            "addon_release_url",
            "pref_branch",
            "pref_name",
            "pref_type",
            "proposed_start_date",
            "proposed_enrollment",
            "proposed_duration",
            "normandy_slug",
            "normandy_id",
            "other_normandy_ids",
            "variants",
            "results",
            "changes",
        )

    def get_results(self, obj):
        return ResultsSerializer(obj).data
