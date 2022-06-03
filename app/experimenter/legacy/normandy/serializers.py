import json

from rest_framework import serializers

from experimenter.legacy.legacy_experiments.api.v1.serializers import PrefTypeField
from experimenter.legacy.legacy_experiments.constants import ExperimentConstants
from experimenter.legacy.legacy_experiments.models import (
    Experiment,
    ExperimentVariant,
    RolloutPreference,
    VariantPreferences,
)


class PrefValueField(serializers.Field):
    def __init__(self, type_field, value_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_field = type_field
        self.value_field = value_field

    def to_representation(self, obj):
        model_fields = (
            type(obj)
            .objects.filter(id=obj.id)
            .values(self.type_field, self.value_field)
            .first()
        )

        pref_type = model_fields[self.type_field]
        value = model_fields[self.value_field]

        if pref_type in (Experiment.PREF_TYPE_BOOL, Experiment.PREF_TYPE_INT):
            return json.loads(value)

        return value


class FilterObjectBucketSampleSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    input = serializers.ReadOnlyField(default=["normandy.userId"])
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
    value = PrefValueField(
        type_field="experiment__pref_type", value_field="value", source="*"
    )

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "value")


class ExperimentRecipeAddonVariantSerializer(serializers.ModelSerializer):
    extensionApiId = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "extensionApiId")

    def get_extensionApiId(self, obj):
        return None


class SingularPreferenceRecipeValueSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="experiment.pref_branch")
    preferenceType = PrefTypeField(source="experiment.pref_type")
    preferenceValue = PrefValueField(
        type_field="experiment__pref_type", value_field="value", source="*"
    )

    class Meta:
        model = ExperimentVariant
        fields = ("preferenceBranchType", "preferenceType", "preferenceValue")


class VariantPreferenceRecipeListSerializer(serializers.ListSerializer):
    def to_representation(self, obj):
        experiment = obj.instance.experiment

        if experiment.is_multi_pref:
            serialized_data = super().to_representation(obj)
            return {entry.pop("pref_name"): entry for entry in serialized_data}

        else:
            preference_values = SingularPreferenceRecipeValueSerializer(obj.instance).data
            return {experiment.pref_name: preference_values}


class VariantPreferenceRecipeSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="pref_branch")
    preferenceType = PrefTypeField(source="pref_type")
    preferenceValue = PrefValueField(
        type_field="pref_type", value_field="pref_value", source="*"
    )

    class Meta:
        list_serializer_class = VariantPreferenceRecipeListSerializer
        model = VariantPreferences
        fields = (
            "preferenceBranchType",
            "preferenceType",
            "preferenceValue",
            "pref_name",
        )


class ExperimentRecipeMultiPrefVariantSerializer(serializers.ModelSerializer):
    preferences = VariantPreferenceRecipeSerializer(many=True)

    class Meta:
        model = ExperimentVariant
        fields = ("preferences", "ratio", "slug")


class ExperimentRecipePrefArgumentsSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="pref_branch")
    slug = serializers.ReadOnlyField(source="recipe_slug")
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")
    preferenceName = serializers.ReadOnlyField(source="pref_name")
    preferenceType = PrefTypeField(source="pref_type")
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


class ExperimentRecipeBranchedArgumentsSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="recipe_slug")
    userFacingName = userFacingDescription = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    branches = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "userFacingName", "userFacingDescription")


class ExperimentRecipeBranchedAddonArgumentsSerializer(
    ExperimentRecipeBranchedArgumentsSerializer
):
    slug = serializers.ReadOnlyField(source="recipe_slug")
    branches = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "userFacingName", "userFacingDescription", "branches")

    def get_branches(self, obj):
        return ExperimentRecipeAddonVariantSerializer(obj.variants, many=True).data


class ExperimentRecipeMultiPrefArgumentsSerializer(
    ExperimentRecipeBranchedArgumentsSerializer
):
    slug = serializers.ReadOnlyField(source="recipe_slug")
    branches = serializers.SerializerMethodField()
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")

    class Meta:
        model = Experiment
        fields = (
            "slug",
            "userFacingName",
            "userFacingDescription",
            "branches",
            "experimentDocumentUrl",
        )

    def get_branches(self, obj):
        return ExperimentRecipeMultiPrefVariantSerializer(obj.variants, many=True).data


class ExperimentRecipeAddonArgumentsSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="addon_experiment_id")
    description = serializers.ReadOnlyField(source="public_description")

    class Meta:
        model = Experiment
        fields = ("name", "description")


class ExperimentRecipeAddonRolloutArgumentsSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="recipe_slug")
    extensionApiId = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "extensionApiId")

    def get_extensionApiId(self, obj):
        return f"TODO: {obj.addon_release_url}"


class RolloutPrefRecipeSerializer(serializers.ModelSerializer):
    preferenceName = serializers.ReadOnlyField(source="pref_name")
    value = PrefValueField(type_field="pref_type", value_field="pref_value", source="*")

    class Meta:
        model = RolloutPreference
        fields = ("preferenceName", "value")


class ExperimentRecipePrefRolloutArgumentsSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="recipe_slug")
    preferences = RolloutPrefRecipeSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ("slug", "preferences")


class ExperimentRecipeMessageVariantSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    groups = serializers.ReadOnlyField(default=[])

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "value", "groups")

    def get_value(self, obj):
        return {}


class ExperimentRecipeMessageArgumentsSerializer(
    ExperimentRecipeBranchedArgumentsSerializer
):
    slug = serializers.ReadOnlyField(source="recipe_slug")
    branches = serializers.SerializerMethodField()
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")

    class Meta:
        model = Experiment
        fields = (
            "slug",
            "userFacingName",
            "userFacingDescription",
            "branches",
            "experimentDocumentUrl",
        )

    def get_branches(self, obj):
        return ExperimentRecipeMessageVariantSerializer(obj.variants, many=True).data


class ExperimentRecipeSerializer(serializers.ModelSerializer):
    action_name = serializers.SerializerMethodField()
    filter_object = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    arguments = serializers.SerializerMethodField()
    experimenter_slug = serializers.ReadOnlyField(source="slug")

    class Meta:
        model = Experiment
        fields = (
            "action_name",
            "name",
            "filter_object",
            "comment",
            "arguments",
            "experimenter_slug",
        )

    def get_action_name(self, obj):
        if obj.use_multi_pref_serializer:
            return "multi-preference-experiment"
        if obj.is_pref_experiment:
            return "preference-experiment"
        elif obj.use_branched_addon_serializer:
            return "branched-addon-study"
        elif obj.is_addon_experiment:
            return "opt-out-study"
        elif obj.is_addon_rollout:
            return "addon-rollout"
        elif obj.is_pref_rollout:
            return "preference-rollout"
        elif obj.is_message_experiment:
            return "messaging-experiment"

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
        if obj.use_multi_pref_serializer:
            return ExperimentRecipeMultiPrefArgumentsSerializer(obj).data
        elif obj.is_pref_experiment:
            return ExperimentRecipePrefArgumentsSerializer(obj).data
        elif obj.use_branched_addon_serializer:
            return ExperimentRecipeBranchedAddonArgumentsSerializer(obj).data
        elif obj.is_addon_experiment:
            return ExperimentRecipeAddonArgumentsSerializer(obj).data
        elif obj.is_addon_rollout:
            return ExperimentRecipeAddonRolloutArgumentsSerializer(obj).data
        elif obj.is_pref_rollout:
            return ExperimentRecipePrefRolloutArgumentsSerializer(obj).data
        elif obj.is_message_experiment:
            return ExperimentRecipeMessageArgumentsSerializer(obj).data

    def get_comment(self, obj):
        comment = f"{obj.client_matching}\n"
        if len(obj.platforms) < len(ExperimentConstants.PLATFORMS_LIST):
            comment += f"Platform: {obj.platforms}\n"
        if obj.windows_versions:
            comment += f"Windows Versions: {obj.windows_versions}\n"
        if obj.profile_age != ExperimentConstants.PROFILES_ALL:
            comment += f"Profile Age: {obj.profile_age}"

        return comment
