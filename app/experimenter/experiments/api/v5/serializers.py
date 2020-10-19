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
    NimbusChangeLogMixin, serializers.ModelSerializer
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


class NimbusBranchUpdateSerializer(NimbusChangeLogMixin, serializers.ModelSerializer):
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
                **control_branch_data
            )
            for branch_data in treatment_branches:
                NimbusBranch.objects.create(
                    experiment=instance, slug=slugify(branch_data["name"]), **branch_data
                )
            instance.save()
        return instance


class NimbusProbeSetUpdateSerializer(NimbusChangeLogMixin, serializers.ModelSerializer):
    probe_sets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=NimbusProbeSet.objects.all()
    )

    class Meta:
        model = NimbusExperiment
        fields = ("probe_sets",)


class NimbusAudienceUpdateSerializer(NimbusChangeLogMixin, serializers.ModelSerializer):
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
