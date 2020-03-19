import json

from rest_framework import serializers
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    VariantPreferences,
    RolloutPreference,
)
from experimenter.experiments.serializers.entities import ChangeLogSerializer
from experimenter.experiments.changelog_utils import generate_change_log


class ChangelogSerializerMixin(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.id:
            self.old_serialized_vals = ChangeLogSerializer(self.instance).data

    def update_changelog(self, instance, validated_data):
        new_serialized_vals = ChangeLogSerializer(instance).data
        user = self.context["request"].user
        changed_data = validated_data.copy()
        generate_change_log(
            self.old_serialized_vals, new_serialized_vals, instance, changed_data, user
        )

        return instance


class PrefValidationMixin(object):

    def validate_pref_branch(self, pref_branch):
        if pref_branch == "Firefox Pref Branch":
            return {"pref_branch": "Please select a branch"}
        return {}

    def validate_multi_preference(self, pref):
        pref_type = pref["pref_type"]
        pref_value = pref["pref_value"]
        field_name = "pref_value"
        errors = {}
        if pref_type == "Firefox Pref Type":
            errors["pref_type"] = "Please select a pref type"

        pref_value_error = self.validate_pref_value(pref_type, pref_value, field_name)
        if pref_value_error:
            errors[field_name] = pref_value_error
        return errors

    def validate_pref_value(self, pref_type, pref_value, field_name):
        if pref_type == "integer":
            try:
                int(pref_value)
            except ValueError:
                return {field_name: "The pref value must be an integer."}

        if pref_type == "boolean":
            if pref_value not in ["true", "false"]:
                return {field_name: "The pref value must be a boolean."}

        if pref_type == "json string":
            try:
                json.loads(pref_value)
            except ValueError:
                return {field_name: "The pref value must be valid JSON."}
        return {}

    def is_pref_valid(self, preferences):
        unique_names = len(
            set([slugify(pref["pref_name"]) for pref in preferences])
        ) == len(preferences)

        return unique_names


class VariantsListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        data = super().to_representation(data)
        initial_fields = set(self.child.fields) - set(["id"])

        if data == []:
            blank_variant = {}
            control_blank_variant = {}
            for field in initial_fields:
                blank_variant[field] = None
                control_blank_variant[field] = None

            blank_variant["is_control"] = False
            blank_variant["ratio"] = 50
            control_blank_variant["is_control"] = True
            control_blank_variant["ratio"] = 50

            data = [control_blank_variant, blank_variant]

        if "preferences" in initial_fields:
            for variant in data:
                if not variant["preferences"]:
                    variant["preferences"] = [{}]

        control_branch = [b for b in data if b["is_control"]][0]
        treatment_branches = sorted(
            [b for b in data if not b["is_control"]], key=lambda b: b.get("id")
        )

        return [control_branch] + treatment_branches


class ExperimentDesignVariantBaseSerializer(serializers.ModelSerializer):
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


class ExperimentDesignVariantPrefSerializer(ExperimentDesignVariantBaseSerializer):
    value = serializers.CharField()

    class Meta(ExperimentDesignVariantBaseSerializer.Meta):
        fields = ["id", "description", "is_control", "name", "ratio", "value"]
        model = ExperimentVariant


class PreferenceListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        data = super().to_representation(data)
        if data == []:
            return [{}]
        return data


class ExperimentDesignBasePreferenceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    pref_name = serializers.CharField(max_length=255)
    pref_type = serializers.CharField(max_length=255)
    pref_branch = serializers.CharField(max_length=255)
    pref_value = serializers.CharField(max_length=255)


class ExperimentDesignBranchVariantPreferencesSerializer(
    ExperimentDesignBasePreferenceSerializer
):

    class Meta:
        model = VariantPreferences
        fields = ["id", "pref_name", "pref_type", "pref_branch", "pref_value"]


class ExperimentDesignBranchMultiPrefSerializer(
    PrefValidationMixin, ExperimentDesignVariantBaseSerializer
):
    preferences = ExperimentDesignBranchVariantPreferencesSerializer(many=True)

    class Meta(ExperimentDesignVariantBaseSerializer.Meta):
        fields = ["id", "description", "is_control", "name", "ratio", "preferences"]
        model = ExperimentVariant

    def validate_preferences(self, data):
        if not self.is_pref_valid(data):
            error_list = [{"pref_name": "Pref name per Branch needs to be unique"}] * len(
                data
            )
            raise serializers.ValidationError(error_list)
        self.validate_value_type_match(data)
        return data

    def validate_value_type_match(self, preferences):
        error_list = []
        for pref in preferences:
            errors = {}
            errors.update(self.validate_pref_branch(pref["pref_branch"]))
            errors.update(self.validate_multi_preference(pref))
            error_list.append(errors)

            if any(error_list):
                raise serializers.ValidationError(error_list)


class ExperimentDesignBaseSerializer(
    ChangelogSerializerMixin, serializers.ModelSerializer
):
    variants = ExperimentDesignVariantBaseSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ("variants",)

    def validate(self, data):
        variants = data.get("variants")

        if variants:
            if sum([variant["ratio"] for variant in variants]) != 100:
                error_list = []
                for variant in variants:
                    error_list.append({"ratio": ["All branch sizes must add up to 100."]})

                raise serializers.ValidationError({"variants": error_list})

            if not self.is_variant_valid(variants):
                error_list = []
                for variant in variants:
                    error_list.append(
                        {"name": [("All branches must have a unique name")]}
                    )

                raise serializers.ValidationError({"variants": error_list})

        return data

    def is_variant_valid(self, variants):

        slugified_nanes = [slugify(variant["name"]) for variant in variants]
        unique_names = len(set(slugified_nanes)) == len(variants)
        non_empty = all(slugified_nanes)

        return unique_names and non_empty

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                variants_data = validated_data.pop("variants", [])
                instance = super().update(instance, validated_data)

            if variants_data:
                existing_variant_ids = set(
                    instance.variants.all().values_list("id", flat=True)
                )
                # Create or update variants
                for variant_data in variants_data:
                    variant_data["experiment"] = instance
                    variant_data["slug"] = slugify(variant_data["name"])
                    ExperimentVariant(**variant_data).save()

                # Delete removed variants
                submitted_variant_ids = set(
                    [v.get("id") for v in variants_data if v.get("id")]
                )
                removed_ids = existing_variant_ids - submitted_variant_ids

                if removed_ids:
                    ExperimentVariant.objects.filter(id__in=removed_ids).delete()

            self.update_changelog(instance, validated_data)

            return instance
        except IntegrityError:
            error_string = (
                "Error: unable to save this change, please contact an experimenter admin"
            )
            error = [{"name": error_string}] * len(variants_data)

            raise serializers.ValidationError({"variants": error})


class ExperimentDesignRolloutPreferenceSerializer(
    ExperimentDesignBasePreferenceSerializer
):

    class Meta:
        model = RolloutPreference
        list_serializer_class = PreferenceListSerializer
        fields = ["id", "pref_name", "pref_type", "pref_value"]


class ExperimentDesignPrefRolloutSerializer(
    PrefValidationMixin, ExperimentDesignBaseSerializer
):
    rollout_type = serializers.ChoiceField(choices=Experiment.ROLLOUT_TYPE_CHOICES)
    preferences = ExperimentDesignRolloutPreferenceSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ("rollout_type", "design", "preferences")

    def validate(self, data):
        data = super().validate(data)

        preferences = data["preferences"]

        if data["rollout_type"] == Experiment.TYPE_PREF:
            invalid_preferences = []
            for preference in preferences:
                pref_invalid = self.validate_multi_preference(preference)

                invalid_preferences.append(pref_invalid)

            if any(invalid_preferences):
                raise serializers.ValidationError({"preferences": invalid_preferences})

        if not self.is_pref_valid(preferences):
            error_list = [{"pref_name": "Pref name needs to be unique"}] * len(
                preferences
            )
            raise serializers.ValidationError({"preferences": error_list})

        return data

    def update(self, instance, validated_data):
        preferences_data = validated_data.pop("preferences", [])
        instance = super().update(instance, validated_data)

        if preferences_data:
            existing_preference_ids = set(
                instance.preferences.all().values_list("id", flat=True)
            )

            submitted_preference_ids = []
            for preference_data in preferences_data:
                preference_data["experiment"] = instance
                pref_id = preference_data.pop("id", None)
                if pref_id:
                    submitted_preference_ids.append(pref_id)
                RolloutPreference.objects.update_or_create(
                    id=pref_id, defaults=preference_data
                )

            removed_ids = existing_preference_ids - set(submitted_preference_ids)

            if removed_ids:
                RolloutPreference.objects.filter(id__in=removed_ids).delete()

        return instance


class ExperimentDesignAddonRolloutSerializer(ExperimentDesignBaseSerializer):
    rollout_type = serializers.ChoiceField(choices=Experiment.ROLLOUT_TYPE_CHOICES)
    addon_release_url = serializers.URLField(max_length=400, allow_null=True)

    class Meta:
        model = Experiment
        fields = ("rollout_type", "design", "addon_release_url")


class ExperimentDesignMultiPrefSerializer(ExperimentDesignBaseSerializer):
    is_multi_pref = serializers.BooleanField()
    variants = ExperimentDesignBranchMultiPrefSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ("is_multi_pref", "variants")

    def update(self, instance, validated_data):
        variant_preferences = [
            (v_d, v_d.pop("preferences")) for v_d in validated_data["variants"]
        ]

        instance = super().update(instance, validated_data)
        existing_pref_ids = list(
            instance.variants.all().values_list("preferences__id", flat=True)
        )
        submitted_pref_ids = []
        for variant_data, prefs in variant_preferences:

            variant = instance.variants.get(name=variant_data["name"])
            for pref in prefs:
                pref["variant_id"] = variant.id
                VariantPreferences(**pref).save()

                if pref.get("id"):
                    pref_id = pref.get("id")
                    submitted_pref_ids.append(pref_id)

        removed_ids = set(existing_pref_ids) - set(submitted_pref_ids)

        if removed_ids:
            VariantPreferences.objects.filter(id__in=removed_ids).delete()

        return instance


class ExperimentChangelogVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentVariant
        fields = ("id", "description", "is_control", "name", "ratio", "value")


class ExperimentDesignPrefSerializer(PrefValidationMixin, ExperimentDesignBaseSerializer):
    is_multi_pref = serializers.BooleanField()
    pref_name = serializers.CharField(max_length=255)
    pref_type = serializers.CharField(max_length=255)
    pref_branch = serializers.CharField(max_length=255)
    variants = ExperimentDesignVariantPrefSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ("is_multi_pref", "pref_name", "pref_type", "pref_branch", "variants")

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
        pref_type = data.get("pref_type", "")
        for variant in variants:
            error_list.append(
                self.validate_pref_value(pref_type, variant["value"], "value")
            )

        if any(error_list):
            raise serializers.ValidationError({"variants": error_list})
        return data


class ExperimentDesignAddonSerializer(ExperimentDesignBaseSerializer):
    addon_release_url = serializers.URLField(max_length=400)
    is_branched_addon = serializers.BooleanField()

    class Meta:
        model = Experiment
        fields = ("addon_release_url", "variants", "is_branched_addon")


class ExperimentDesignGenericSerializer(ExperimentDesignBaseSerializer):
    design = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = Experiment
        fields = ("design", "variants")


class ExperimentBranchedAddonVariantSerializer(ExperimentDesignVariantBaseSerializer):
    addon_release_url = serializers.URLField(max_length=400)

    class Meta(ExperimentDesignVariantBaseSerializer.Meta):
        model = ExperimentVariant
        fields = ["addon_release_url", "id", "description", "is_control", "name", "ratio"]


class ExperimentDesignBranchedAddonSerializer(ExperimentDesignBaseSerializer):
    variants = ExperimentBranchedAddonVariantSerializer(many=True)
    is_branched_addon = serializers.BooleanField()

    class Meta:
        model = Experiment
        fields = ("is_branched_addon", "variants")
