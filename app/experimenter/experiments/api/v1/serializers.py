import time

from rest_framework import serializers

from experimenter.base.serializers import CountrySerializer, LocaleSerializer
from experimenter.experiments.models import (
    Experiment,
    ExperimentChangeLog,
    ExperimentVariant,
    RolloutPreference,
    VariantPreferences,
)
from experimenter.projects.models import Project


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


class ExperimentVariantPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantPreferences
        fields = ("pref_name", "pref_type", "pref_branch", "pref_value")


class ExperimentRolloutPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolloutPreference
        fields = ("pref_name", "pref_type", "pref_value")


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("slug",)


class ExperimentVariantSerializer(serializers.ModelSerializer):
    preferences = ExperimentVariantPreferenceSerializer(many=True, required=False)

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
            "message_targeting",
            "message_threshold",
            "message_triggers",
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
    normandy_slug = serializers.CharField(source="recipe_slug")

    class Meta:
        model = Experiment
        fields = (
            "experiment_url",
            "type",
            "name",
            "slug",
            "public_description",
            "status",
            "client_matching",
            "locales",
            "countries",
            "platforms",
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
            "is_high_population",
            "variants",
            "results",
            "changes",
        )

    def get_results(self, obj):
        return ResultsSerializer(obj).data
