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
            "addon_release_url",
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
            "results_url",
            "results_initial",
            "results_lessons_learned",
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
    input = serializers.ReadOnlyField(default=["normandy.recipe.id", "normandy.userId"])
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


class ExperimentRecipeAddonVariantSerializer(serializers.ModelSerializer):
    extensionApiId = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "extensionApiId")

    def get_extensionApiId(self, obj):
        return None


class ExperimentRecipeMultiPrefVariantSerializer(serializers.ModelSerializer):
    preferences = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("preferences", "ratio", "slug")

    def get_preferences(self, obj):
        preference_values = {}
        preference_values["preferenceBranchType"] = obj.experiment.pref_branch
        preference_values["preferenceType"] = PrefTypeField().to_representation(
            obj.experiment.pref_type
        )
        preference_values["preferenceValue"] = obj.value

        preferences = {}
        preferences[obj.experiment.pref_key] = preference_values

        return preferences


class ExperimentRecipePrefArgumentsSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="pref_branch")
    slug = serializers.ReadOnlyField(source="normandy_slug")
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")
    preferenceName = serializers.ReadOnlyField(source="pref_key")
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
    slug = serializers.ReadOnlyField(source="normandy_slug")
    userFacingName = userFacingDescription = serializers.ReadOnlyField(
        source="public_name"
    )
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    branches = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "userFacingName", "userFacingDescription")


class ExperimentRecipeBranchedAddonArgumentsSerializer(
    ExperimentRecipeBranchedArgumentsSerializer
):
    branches = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "userFacingName", "userFacingDescription", "branches")

    def get_branches(self, obj):
        return ExperimentRecipeAddonVariantSerializer(obj.variants, many=True).data


class ExperimentRecipeMultiPrefArgumentsSerializer(
    ExperimentRecipeBranchedArgumentsSerializer
):
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
        if obj.is_multi_pref:
            return "multi-preference-experiment"
        if obj.is_pref_experiment:
            return "preference-experiment"
        elif obj.use_branched_addon_serializer:
            return "branched-addon-study"
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
        if obj.is_multi_pref:
            return ExperimentRecipeMultiPrefArgumentsSerializer(obj).data
        elif obj.is_pref_experiment:
            return ExperimentRecipePrefArgumentsSerializer(obj).data
        elif obj.use_branched_addon_serializer:
            return ExperimentRecipeBranchedAddonArgumentsSerializer(obj).data
        elif obj.is_addon_experiment:
            return ExperimentRecipeAddonArgumentsSerializer(obj).data

    def get_comment(self, obj):
        return f"Platform: {obj.platform}\n{obj.client_matching}"


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
            raise serializers.ValidationError("This experiment name already exists.")

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


class VariantsListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        data = super().to_representation(data)

        if data == []:
            blank_variant = {}
            control_blank_variant = {}
            initial_fields = set(self.child.fields) - set(["id"])
            for field in initial_fields:
                blank_variant[field] = None
                control_blank_variant[field] = None

            blank_variant["is_control"] = False
            blank_variant["ratio"] = 50
            control_blank_variant["is_control"] = True
            control_blank_variant["ratio"] = 50

            data = [control_blank_variant, blank_variant]

        control_branch = [b for b in data if b["is_control"]][0]
        treatment_branches = sorted(
            [b for b in data if not b["is_control"]], key=lambda b: b.get("id")
        )

        return [control_branch] + treatment_branches


class ExperimentDesignBranchBaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    description = serializers.CharField()
    is_control = serializers.BooleanField()
    name = serializers.CharField(max_length=255)
    ratio = serializers.IntegerField()

    def validate_ratio(self, value):
        if 1 <= value <= 100:
            return value

        raise serializers.ValidationError(["Branch sizes must be between 1 and 100."])

    class Meta:
        list_serializer_class = VariantsListSerializer
        fields = ["id", "description", "is_control", "name", "ratio"]
        model = ExperimentVariant


class ExperimentDesignBranchPrefSerializer(ExperimentDesignBranchBaseSerializer):
    value = serializers.CharField()

    class Meta(ExperimentDesignBranchBaseSerializer.Meta):
        fields = ["id", "description", "is_control", "name", "ratio", "value"]
        model = ExperimentVariant


class ExperimentDesignBaseSerializer(serializers.ModelSerializer):
    type = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=255
    )
    variants = ExperimentDesignBranchBaseSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ("type", "variants")

    def validate(self, data):
        variants = data["variants"]

        if sum([variant["ratio"] for variant in variants]) != 100:
            error_list = []
            for variant in variants:
                error_list.append({"ratio": ["All branch sizes must add up to 100."]})

            raise serializers.ValidationError({"variants": error_list})

        if not self.is_variant_valid(variants):
            error_list = []
            for variant in variants:
                error_list.append(
                    {
                        "name": [
                            (
                                "All branches must have a unique name "
                                "and not contain special characters."
                            )
                        ]
                    }
                )

            raise serializers.ValidationError({"variants": error_list})

        return data

    def is_variant_valid(self, variants):
        unique_names = len(
            set([slugify(variant["name"]) for variant in variants])
        ) == len(variants)

        all_contains_alphanumeric_and_spaces = all(
            Experiment.EXPERIMENT_VARIANT_NAME_REGEX.match(variant["name"])
            for variant in variants
        )

        return unique_names and all_contains_alphanumeric_and_spaces

    def update(self, instance, validated_data):
        variants_data = validated_data.pop("variants")
        instance = super().update(instance, validated_data)

        existing_variant_ids = set(instance.variants.all().values_list("id", flat=True))

        # Create or update variants
        for variant_data in variants_data:
            variant_data["experiment"] = instance
            variant_data["slug"] = slugify(variant_data["name"])
            ExperimentVariant(**variant_data).save()

        # Delete removed variants
        submitted_variant_ids = set([v.get("id") for v in variants_data if v.get("id")])
        removed_ids = existing_variant_ids - submitted_variant_ids

        if removed_ids:
            ExperimentVariant.objects.filter(id__in=removed_ids).delete()

        return instance


class ExperimentDesignPrefSerializer(ExperimentDesignBaseSerializer):
    pref_key = serializers.CharField(max_length=255)
    pref_type = serializers.CharField(max_length=255)
    pref_branch = serializers.CharField(max_length=255)
    variants = ExperimentDesignBranchPrefSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ("type", "pref_key", "pref_type", "pref_branch", "variants")

    def validate_pref_type(self, value):
        if value == "Firefox Pref Type":
            raise serializers.ValidationError(["Please select a type."])

        return value

    def validate_pref_branch(self, value):
        if value == "Firefox Pref Branch":
            raise serializers.ValidationError(["Please select a branch."])

        return value

    def validate(self, data):
        super().validate(data)

        variants = data["variants"]

        if not len(set(variant["value"] for variant in variants)) == len(variants):
            error_list = []
            for variant in variants:
                error_list.append(
                    {"value": ["All branches must have a unique pref value."]}
                )

            raise serializers.ValidationError({"variants": error_list})

        error_list = []
        for variant in variants:
            if data.get("pref_type", "") == "integer":
                try:
                    int(variant["value"])
                except ValueError:
                    error_list.append({"value": ["The pref value must be an integer."]})
                else:
                    error_list.append({"value": ""})

            if data.get("pref_type", "") == "boolean":
                if variant["value"] not in ["true", "false"]:
                    error_list.append({"value": ["The pref value must be a boolean."]})

                else:
                    error_list.append({"value": ""})

            if data.get("pref_type", "") == "json string":
                try:
                    json.loads(variant["value"])
                except ValueError:
                    error_list.append({"value": ["The pref value must be valid JSON."]})
                else:
                    error_list.append({"value": ""})

        for entry in error_list:
            if entry["value"] != "":
                raise serializers.ValidationError({"variants": error_list})
        return data


class ExperimentDesignAddonSerializer(ExperimentDesignBaseSerializer):
    addon_experiment_id = serializers.CharField(max_length=255)
    addon_release_url = serializers.URLField(max_length=400)
    is_branched_addon = serializers.BooleanField()

    class Meta:
        model = Experiment
        fields = ("type", "addon_release_url", "addon_experiment_id", "variants", "is_branched_addon")

    def validate_addon_experiment_id(self, value):
        existing = Experiment.objects.filter(addon_experiment_id=value)

        if self.instance:
            existing = existing.exclude(id=self.instance.id)

        if existing.exists():
            raise serializers.ValidationError(
                ["An experiment with this Addon Experiment Name already exists."]
            )

        return value


class ExperimentDesignGenericSerializer(ExperimentDesignBaseSerializer):
    design = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = Experiment
        fields = ("type", "design", "variants")


class ExperimentBranchedAddonBranchSerializer(ExperimentDesignBranchBaseSerializer):
    addon_release_url = serializers.URLField(max_length=400)

    class Meta:
        model = ExperimentVariant
        fields = ["addon_release_url", "id", "description", "is_control", "name", "ratio"]


class ExperimentDesignBranchedAddonSerializer(serializers.ModelSerializer):
    variants = ExperimentBranchedAddonBranchSerializer(many=True)
    is_branched_addon = serializers.BooleanField()

    class Meta:
        model = Experiment
        fields = ("type", "is_branched_addon", "variants")

    def update(self, instance, validated_data):
        variants_data = validated_data.pop("variants")
        instance = super().update(instance, validated_data)

        existing_variant_ids = set(instance.variants.all().values_list("id", flat=True))

        # Create or update variants
        for variant_data in variants_data:
            variant_data["experiment"] = instance
            variant_data["slug"] = slugify(variant_data["name"])
            ExperimentVariant(**variant_data).save()

        # Delete removed variants
        submitted_variant_ids = set([v.get("id") for v in variants_data if v.get("id")])
        removed_ids = existing_variant_ids - submitted_variant_ids

        if removed_ids:
            ExperimentVariant.objects.filter(id__in=removed_ids).delete()

        return instance
