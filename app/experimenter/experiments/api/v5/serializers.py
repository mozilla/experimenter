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
