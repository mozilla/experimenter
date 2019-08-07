import time
import json
from rest_framework import serializers
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import Q

from experimenter.base.models import Country, Locale
from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
)


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


class ExperimentVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentVariant
        fields = (
            "description",
            "is_control",
            "name",
            "ratio",
            "slug",
            "value",
        )


class LocaleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Locale
        fields = ("code", "name")


class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = ("code", "name")


class ExperimentChangeLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentChangeLog
        fields = ("changed_on", "pretty_status", "new_status", "old_status")


class ChangeLogSerializer(serializers.ModelSerializer):
    variants = ExperimentVariantSerializer(many=True, required=False)
    locales = LocaleSerializer(many=True, required=False)
    countries = CountrySerializer(many=True, required=False)
    pref_type = PrefTypeField()

    class Meta:
        model = Experiment
        fields = (
            "type",
            "status",
            "owner",
            "name",
            "short_description",
            "related_work",
            "proposed_start_date",
            "proposed_duration",
            "proposed_enrollment",
            "addon_experiment_id",
            "addon_release_url",
            "pref_key",
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
            "platform",
            "objectives",
            "analysis",
            "analysis_owner",
            "survey_required",
            "survey_urls",
            "survey_instructions",
            "engineering_owner",
            "bugzilla_id",
            "slug",
            "normandy_slug",
            "normandy_id",
            "data_science_bugzilla_url",
            "feature_bugzilla_url",
            "risk_internal_only",
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

    class Meta:
        model = Experiment
        fields = (
            "experiment_url",
            "type",
            "name",
            "slug",
            "status",
            "short_description",
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
            "objectives",
            "analysis_owner",
            "analysis",
            "addon_experiment_id",
            "addon_release_url",
            "pref_branch",
            "pref_key",
            "pref_type",
            "proposed_start_date",
            "proposed_enrollment",
            "proposed_duration",
            "variants",
            "changes",
        )


class FilterObjectBucketSampleSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    input = serializers.ReadOnlyField(
        default=["normandy.recipe.id", "normandy.userId"]
    )
    start = serializers.ReadOnlyField(default=0)
    count = serializers.SerializerMethodField()
    total = serializers.ReadOnlyField(default=10000)

    class Meta:
        model = Experiment
        fields = ("type", "input", "start", "count", "total")

    def get_type(self, obj):
        return "bucketSample"

    def get_count(self, obj):
        return int(obj.population_percent * 100)


class FilterObjectChannelSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    channels = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "channels")

    def get_type(self, obj):
        return "channel"

    def get_channels(self, obj):
        return [obj.firefox_channel.lower()]


class FilterObjectVersionsSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "versions")

    def get_type(self, obj):
        return "version"

    def get_versions(self, obj):
        return obj.versions_integer_list


class FilterObjectLocaleSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    locales = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "locales")

    def get_type(self, obj):
        return "locale"

    def get_locales(self, obj):
        return list(obj.locales.all().values_list("code", flat=True))


class FilterObjectCountrySerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "countries")

    def get_type(self, obj):
        return "country"

    def get_countries(self, obj):
        return list(obj.countries.all().values_list("code", flat=True))


class ExperimentRecipeVariantSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "value")

    def get_value(self, obj):
        pref_type = obj.experiment.pref_type
        if pref_type in (Experiment.PREF_TYPE_BOOL, Experiment.PREF_TYPE_INT):
            return json.loads(obj.value)

        return obj.value


class ExperimentRecipePrefArgumentsSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="pref_branch")
    slug = serializers.ReadOnlyField(source="normandy_slug")
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")
    preferenceName = serializers.ReadOnlyField(source="pref_key")
    preferenceType = serializers.ReadOnlyField(source="pref_type")
    branches = ExperimentRecipeVariantSerializer(many=True, source="variants")

    class Meta:
        model = Experiment
        fields = (
            "preferenceBranchType",
            "slug",
            "experimentDocumentUrl",
            "preferenceName",
            "preferenceType",
            "branches",
        )


class ExperimentRecipeAddonArgumentsSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="addon_experiment_id")
    description = serializers.ReadOnlyField(source="public_description")

    class Meta:
        model = Experiment
        fields = ("name", "description")


class ExperimentRecipeSerializer(serializers.ModelSerializer):
    action_name = serializers.SerializerMethodField()
    filter_object = serializers.SerializerMethodField()
    comment = serializers.ReadOnlyField(source="client_matching")
    arguments = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = (
            "action_name",
            "name",
            "filter_object",
            "comment",
            "arguments",
        )

    def get_action_name(self, obj):
        if obj.is_pref_experiment:
            return "preference-experiment"
        elif obj.is_addon_experiment:
            return "opt-out-study"

    def get_filter_object(self, obj):
        filter_objects = [
            FilterObjectBucketSampleSerializer(obj).data,
            FilterObjectChannelSerializer(obj).data,
            FilterObjectVersionsSerializer(obj).data,
        ]

        if obj.locales.count():
            filter_objects.append(FilterObjectLocaleSerializer(obj).data)

        if obj.countries.count():
            filter_objects.append(FilterObjectCountrySerializer(obj).data)

        return filter_objects

    def get_arguments(self, obj):
        if obj.is_pref_experiment:
            return ExperimentRecipePrefArgumentsSerializer(obj).data
        elif obj.is_addon_experiment:
            return ExperimentRecipeAddonArgumentsSerializer(obj).data


class ExperimentCloneSerializer(serializers.ModelSerializer):
    clone_url = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("name", "clone_url")

    def validate_name(self, value):
        existing_slug_or_name = Experiment.objects.filter(
            Q(slug=slugify(value)) | Q(name=value)
        )

        if existing_slug_or_name:
            raise serializers.ValidationError(
                "This experiment name already exists."
            )

        if slugify(value):
            return value
        else:
            raise serializers.ValidationError("That's an invalid name.")

    def get_clone_url(self, obj):
        return reverse("experiments-detail", kwargs={"slug": obj.slug})

    def update(self, instance, validated_data):
        user = self.context["request"].user
        name = validated_data.get("name")

        return instance.clone(name, user)
