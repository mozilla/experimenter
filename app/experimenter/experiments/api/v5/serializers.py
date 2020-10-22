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
    class Meta:
        model = NimbusExperiment
        fields = (
            "name",
            "slug",
            "application",
            "public_description",
            "hypothesis",
        )

    slug = serializers.ReadOnlyField()

    def validate(self, data):
        if data.get("slug") is None:
            slug = slugify(data.get("name"))

            if not slug:
                raise serializers.ValidationError(
                    {"name": ["Name needs to contain alphanumeric characters"]}
                )
            if (
                self.instance is None
                and slug
                and NimbusExperiment.objects.filter(slug=slug).exists()
            ):
                raise serializers.ValidationError(
                    {
                        "name": [
                            "Name maps to a pre-existing slug, please choose another name"
                        ]
                    }
                )

        return data

    def create(self, validated_data):
        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
            }
        )
        experiment = super().create(validated_data)
        return experiment


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
                    experiment=instance, slug=slugify(branch_data["name"]), **branch_data
                )
            instance.save()
        return instance


class NimbusProbeSetUpdateSerializer(
    NimbusChangeLogMixin, NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    probe_sets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=NimbusProbeSet.objects.all()
    )

    class Meta:
        model = NimbusExperiment
        fields = ("probe_sets",)


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
