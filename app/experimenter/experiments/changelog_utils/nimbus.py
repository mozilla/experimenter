from rest_framework import serializers

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusChangeLog,
    NimbusExperiment,
    NimbusFeatureConfig,
)
from experimenter.experiments.models.nimbus import NimbusBranchFeatureValue


class NimbusFeatureConfigChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusFeatureConfig
        exclude = ("id",)


class NimbusBranchFeatureValueChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusBranchFeatureValue
        exclude = ("id",)


class NimbusBranchChangeLogSerializer(serializers.ModelSerializer):
    feature_values = NimbusBranchFeatureValueChangeLogSerializer(many=True)

    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment")


class NimbusExperimentChangeLogSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    reference_branch = NimbusBranchChangeLogSerializer()
    branches = NimbusBranchChangeLogSerializer(many=True)
    feature_configs = NimbusFeatureConfigChangeLogSerializer(many=True)
    owner = serializers.SlugRelatedField(read_only=True, slug_field="email")
    projects = serializers.SlugRelatedField(many=True, read_only=True, slug_field="slug")

    class Meta:
        model = NimbusExperiment
        exclude = ("id",)


def generate_nimbus_changelog(experiment, changed_by, message):
    latest_change = experiment.changes.latest_change()
    experiment_data = dict(NimbusExperimentChangeLogSerializer(experiment).data)

    old_status = None
    old_status_next = None
    old_publish_status = None
    published_dto_changed = False
    if latest_change:
        old_status = latest_change.new_status
        old_status_next = latest_change.new_status_next
        old_publish_status = latest_change.new_publish_status
        published_dto_changed = latest_change.experiment_data.get(
            "published_dto"
        ) != experiment_data.get("published_dto")

    return NimbusChangeLog.objects.create(
        experiment=experiment,
        old_status=old_status,
        old_status_next=old_status_next,
        old_publish_status=old_publish_status,
        new_status=experiment.status,
        new_status_next=experiment.status_next,
        new_publish_status=experiment.publish_status,
        changed_by=changed_by,
        experiment_data=experiment_data,
        published_dto_changed=published_dto_changed,
        message=message,
    )
