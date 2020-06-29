import time

from rest_framework import serializers

from experimenter.base.serializers import CountrySerializer, LocaleSerializer
from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
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
            "variants",
            "results",
            "changes",
            "telemetry_event_category",
            "telemetry_event_method",
            "telemetry_event_object",
            "telemetry_event_value",
        )

    def get_results(self, obj):
        return ResultsSerializer(obj).data


class ExperimentCSVSerializer(serializers.ModelSerializer):
    analysis_owner = serializers.SlugRelatedField(read_only=True, slug_field="email")
    owner = serializers.SlugRelatedField(read_only=True, slug_field="email")
    parent = serializers.SlugRelatedField(read_only=True, slug_field="experiment_url")
    projects = serializers.SerializerMethodField()
    related_to = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = (
            "name",
            "type",
            "status",
            "experiment_url",
            "public_description",
            "owner",
            "analysis_owner",
            "engineering_owner",
            "short_description",
            "objectives",
            "parent",
            "projects",
            "data_science_issue_url",
            "feature_bugzilla_url",
            "firefox_channel",
            "normandy_slug",
            "proposed_duration",
            "proposed_start_date",
            "related_to",
            "related_work",
            "results_initial",
            "results_url",
        )

    def get_projects(self, obj):
        return ", ".join([p.name for p in obj.projects.order_by("name")])

    def get_related_to(self, obj):
        return ", ".join([e.experiment_url for e in obj.related_to.order_by("slug")])


class ExperimentRapidBranchesSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("slug", "ratio", "value")

    def get_value(self, obj):
        # placeholder value
        return None


class ExperimentRapidArgumentSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="normandy_slug")
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    active = serializers.ReadOnlyField(default=True)
    isEnrollmentPaused = serializers.ReadOnlyField(default=False)
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    bucketConfig = serializers.SerializerMethodField()
    startDate = serializers.SerializerMethodField()
    endDate = serializers.ReadOnlyField(default=None)
    branches = ExperimentRapidBranchesSerializer(many=True, source="variants")
    referenceBranch = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = (
            "slug",
            "userFacingName",
            "userFacingDescription",
            "active",
            "isEnrollmentPaused",
            "features",
            "proposedEnrollment",
            "bucketConfig",
            "startDate",
            "endDate",
            "branches",
            "referenceBranch",
        )

    def get_bucketConfig(self, obj):
        return {
            "randomizationUnit": "normandy_id",
            "namespace": "",
            "start": 0,
            "count": 0,
            "total": 10000,
        }

    def get_referenceBranch(self, obj):
        control_branch = obj.variants.get(is_control=True)
        return control_branch.slug

    def get_startDate(self, obj):
        # placeholder value
        return obj.start_date.isoformat()


class ExperimentRapidRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="normandy_slug")
    arguments = ExperimentRapidArgumentSerializer(source="*")
    filter_expression = serializers.ReadOnlyField(source="audience")
    enabled = serializers.ReadOnlyField(default=True)

    class Meta:
        model = Experiment
        fields = ("id", "arguments", "filter_expression", "enabled")
