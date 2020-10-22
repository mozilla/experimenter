from django.contrib.auth import get_user_model
from rest_framework import serializers

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusChangeLog,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusProbeSet,
)
from experimenter.projects.models import Project


class NimbusFeatureConfigChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusFeatureConfig
        exclude = ("id",)


class NimbusBranchChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment")


class NimbusExperimentChangeLogSerializer(serializers.ModelSerializer):
    reference_branch = NimbusBranchChangeLogSerializer()
    branches = NimbusBranchChangeLogSerializer(many=True)
    probe_sets = serializers.SlugRelatedField(
        many=True, queryset=NimbusProbeSet.objects.all(), slug_field="slug"
    )
    feature_config = NimbusFeatureConfigChangeLogSerializer()
    owner = serializers.SlugRelatedField(
        queryset=get_user_model().objects.all(), slug_field="email"
    )
    projects = serializers.SlugRelatedField(
        many=True, queryset=Project.objects.all(), slug_field="slug"
    )

    class Meta:
        model = NimbusExperiment
        exclude = ("id",)


def generate_nimbus_changelog(experiment, changed_by):
    latest_change = experiment.latest_change()
    experiment_data = dict(NimbusExperimentChangeLogSerializer(experiment).data)

    old_status = None
    if latest_change:
        old_status = latest_change.new_status

    NimbusChangeLog.objects.create(
        experiment=experiment,
        old_status=old_status,
        new_status=experiment.status,
        changed_by=changed_by,
        experiment_data=experiment_data,
    )
