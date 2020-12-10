import json

import jsonschema
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.models.nimbus import (
    NimbusBranch,
    NimbusFeatureConfig,
    NimbusProbeSet,
)


class NimbusStatusRestrictionMixin:
    required_status = NimbusExperiment.Status.DRAFT

    def validate(self, data):
        data = super().validate(data)
        if self.instance and self.instance.status != self.required_status:
            status = self.instance.status
            raise serializers.ValidationError(
                {
                    "experiment": [
                        f"Nimbus Experiment has status '{status}', but can only "
                        f"be changed when set to '{self.required_status}'."
                    ]
                }
            )
        return data


class NimbusChangeLogMixin:
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        generate_nimbus_changelog(experiment, self.context["user"])
        return experiment


class NimbusBranchSerializer(NimbusChangeLogMixin, serializers.ModelSerializer):
    def validate_name(self, value):
        slug_name = slugify(value)
        if not slug_name:
            raise serializers.ValidationError(
                "Name needs to contain alphanumeric characters."
            )
        return value

    def validate(self, data):
        data = super().validate(data)
        if data.get("feature_enabled", False) and "feature_value" not in data:
            raise serializers.ValidationError(
                {
                    "feature_enabled": (
                        "feature_value must be specified if feature_enabled is True."
                    )
                }
            )
        if data.get("feature_value") and "feature_enabled" not in data:
            raise serializers.ValidationError(
                {
                    "feature_value": (
                        "feature_enabled must be specificed to include a feature_value."
                    )
                }
            )
        return data

    class Meta:
        model = NimbusBranch
        fields = (
            "name",
            "description",
            "ratio",
            "feature_enabled",
            "feature_value",
        )


class NimbusExperimentOverviewSerializer(
    NimbusChangeLogMixin, NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    slug = serializers.ReadOnlyField()

    class Meta:
        model = NimbusExperiment
        fields = (
            "name",
            "slug",
            "application",
            "public_description",
            "hypothesis",
        )

    def validate_name(self, name):
        slug = slugify(name)

        if not slug:
            raise serializers.ValidationError(
                "Name needs to contain alphanumeric characters"
            )

        if (
            self.instance is None
            and slug
            and NimbusExperiment.objects.filter(slug=slug).exists()
        ):
            raise serializers.ValidationError(
                "Name maps to a pre-existing slug, please choose another name"
            )

        return name

    def validate_hypothesis(self, hypothesis):
        if hypothesis.strip() == NimbusExperiment.HYPOTHESIS_DEFAULT.strip():
            raise serializers.ValidationError(
                "Please describe the hypothesis of your experiment."
            )
        return hypothesis

    def create(self, validated_data):
        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
                "owner": self.context["user"],
            }
        )
        return super().create(validated_data)


class NimbusBranchUpdateSerializer(
    NimbusChangeLogMixin, NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    reference_branch = NimbusBranchSerializer()
    treatment_branches = NimbusBranchSerializer(many=True)
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        allow_null=True,
    )

    class Meta:
        model = NimbusExperiment
        fields = (
            "feature_config",
            "reference_branch",
            "treatment_branches",
        )

    def _validate_feature_value_against_schema(self, schema, value):
        try:
            json_value = json.loads(value)
        except json.JSONDecodeError as exc:
            return [exc.msg]
        try:
            jsonschema.validate(json_value, schema)
        except jsonschema.ValidationError as exc:
            return [exc.message]

    def validate(self, data):
        data = super().validate(data)
        # Determine if we require a feature_config
        feature_config_required = data["reference_branch"].get("feature_enabled", False)
        for branch in data["treatment_branches"]:
            branch_required = branch.get("feature_enabled", False)
            feature_config_required = feature_config_required or branch_required
        feature_config = data.get("feature_config", None)
        if feature_config_required and not feature_config:
            raise serializers.ValidationError(
                {
                    "feature_config": [
                        "Feature Config required when a branch has feature enabled."
                    ]
                }
            )

        if not feature_config or not feature_config.schema or not self.instance:
            return data

        schema = json.loads(feature_config.schema)
        error_result = {}
        if data["reference_branch"].get("feature_enabled"):
            errors = self._validate_feature_value_against_schema(
                schema, data["reference_branch"]["feature_value"]
            )
            if errors:
                error_result["reference_branch"] = {"feature_value": errors}

        treatment_branches_errors = []
        for branch_data in data["treatment_branches"]:
            branch_error = None
            if branch_data.get("feature_enabled", False):
                errors = self._validate_feature_value_against_schema(
                    schema, branch_data["feature_value"]
                )
                if errors:
                    branch_error = {"feature_value": errors}
            treatment_branches_errors.append(branch_error)

        if any(x is not None for x in treatment_branches_errors):
            error_result["treatment_branches"] = treatment_branches_errors

        if error_result:
            raise serializers.ValidationError(error_result)
        return data

    def update(self, experiment, data):
        control_branch_data = data.pop("reference_branch")
        treatment_branches = data.pop("treatment_branches")
        with transaction.atomic():
            instance = super().update(experiment, data)
            NimbusBranch.objects.filter(experiment=instance).delete()
            experiment.reference_branch = NimbusBranch.objects.create(
                experiment=instance,
                slug=slugify(control_branch_data["name"]),
                **control_branch_data,
            )
            for branch_data in treatment_branches:
                NimbusBranch.objects.create(
                    experiment=instance,
                    slug=slugify(branch_data["name"]),
                    **branch_data,
                )
            instance.save()
        return instance


class NimbusProbeSetUpdateSerializer(
    NimbusChangeLogMixin, NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    primary_probe_sets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=NimbusProbeSet.objects.all()
    )

    secondary_probe_sets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=NimbusProbeSet.objects.all()
    )

    class Meta:
        model = NimbusExperiment
        fields = ("primary_probe_sets", "secondary_probe_sets")

    def validate_primary_probe_sets(self, value):
        if len(value) > NimbusExperiment.MAX_PRIMARY_PROBE_SETS:
            raise serializers.ValidationError(
                "Exceeded maximum primary probe set limit of "
                f"{NimbusExperiment.MAX_PRIMARY_PROBE_SETS}."
            )
        return value

    def validate(self, data):
        """Validate the probe sets don't overlap and have no more than the max
        number of primary probesets.

        Note that the default DRF validation ensures all the probe id's are valid and
        it will not save overlapping probesets. It does not however throw an error with
        overlapping probesets, so that is checked explicitly here.

        """
        data = super().validate(data)
        primary_probe_sets = set(data["primary_probe_sets"])
        secondary_probe_sets = set(data["secondary_probe_sets"])
        if primary_probe_sets.intersection(secondary_probe_sets):
            raise serializers.ValidationError(
                {
                    "primary_probe_sets": (
                        "Primary probe sets cannot overlap with secondary probe sets."
                    )
                }
            )
        return data

    def update(self, experiment, data):
        primary_probe_sets = data.pop("primary_probe_sets")
        secondary_probe_sets = data.pop("secondary_probe_sets")
        with transaction.atomic():
            experiment = super().update(experiment, data)
            experiment.probe_sets.clear()
            for probe_set in primary_probe_sets:
                experiment.probe_sets.add(
                    probe_set, through_defaults={"is_primary": True}
                )
            for probe_set in secondary_probe_sets:
                experiment.probe_sets.add(
                    probe_set, through_defaults={"is_primary": False}
                )
            experiment.save()
        return experiment


class NimbusAudienceUpdateSerializer(
    NimbusChangeLogMixin, NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    class Meta:
        model = NimbusExperiment
        fields = (
            "channels",
            "firefox_min_version",
            "population_percent",
            "proposed_duration",
            "proposed_enrollment",
            "targeting_config_slug",
            "total_enrolled_clients",
        )

    def validate_channels(self, value):
        # If we have an instance, we can validate the channels against the application
        if value and self.instance and self.instance.application:
            valid_channels = set(
                channel.value
                for channel in NimbusExperiment.ApplicationChannels[
                    self.instance.application
                ]
            )
            if not valid_channels.issuperset(set(value)):
                raise serializers.ValidationError(
                    "Invalid channels for experiment application."
                )
        return value


class NimbusStatusUpdateSerializer(
    NimbusChangeLogMixin, NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    def validate_status(self, value):
        if value != NimbusExperiment.Status.REVIEW:
            raise serializers.ValidationError(
                "Nimbus Experiments can only transition from DRAFT to REVIEW."
            )
        return value

    class Meta:
        model = NimbusExperiment
        fields = ("status",)


class NimbusReadyForReviewSerializer(
    NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    public_description = serializers.CharField(required=True)
    proposed_duration = serializers.IntegerField(required=True)
    proposed_enrollment = serializers.IntegerField(required=True)
    population_percent = serializers.DecimalField(7, 4, required=True)
    firefox_min_version = serializers.ChoiceField(
        NimbusExperiment.Version.choices, required=True
    )
    application = serializers.ChoiceField(
        NimbusExperiment.Application.choices, required=True
    )
    hypothesis = serializers.CharField(required=True)
    targeting_config_slug = serializers.ChoiceField(
        NimbusExperiment.TargetingConfig.choices, required=True
    )
    reference_branch = NimbusBranchSerializer(required=True)
    treatment_branches = NimbusBranchSerializer(many=True)
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        allow_null=True,
    )

    class Meta:
        model = NimbusExperiment
        exclude = ("id",)

    def validate_hypothesis(self, value):
        if value == NimbusExperiment.HYPOTHESIS_DEFAULT.strip():
            raise serializers.ValidationError("Hypothesis cannot be the default value.")
        return value
