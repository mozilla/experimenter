from django.utils import timezone
from rest_framework import serializers

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusChangeLog,
    NimbusExperiment,
    NimbusFeatureConfig,
)


class NimbusFeatureConfigChangeLogSerializer(serializers.ModelSerializer):
    schema = serializers.SerializerMethodField()

    class Meta:
        model = NimbusFeatureConfig
        exclude = ("id",)

    def get_schema(self, obj):
        return obj.schemas.get(version=None).schema


class NimbusBranchFeatureValueChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusBranchFeatureValue
        exclude = ("id",)


class NimbusBranchChangeLogSerializer(serializers.ModelSerializer):
    feature_values = NimbusBranchFeatureValueChangeLogSerializer(many=True)

    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment")


class NimbusChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusChangeLog
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


def generate_nimbus_changelog(experiment, changed_by, message, changed_on=None):
    latest_change = experiment.changes.latest_change()
    experiment_data = dict(NimbusExperimentChangeLogSerializer(experiment).data)

    if not changed_on:
        changed_on = timezone.now()

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
        changed_on=changed_on,
    )


def get_formatted_change_object(field_name, field_diff, changelog, timestamp):
    event = NimbusConstants.ChangeEvent.find_enum_by_key(field_name.upper())
    field_display_name = (
        event.display_name
        if event.value != NimbusConstants.ChangeEvent.TRIVIAL.value
        else field_name
    )

    old_value = field_diff["old_value"]
    new_value = field_diff["new_value"]

    if event.value == "DATE_TIME":
        if old_value is not None:
            old_value = old_value.strftime("%B %d, %Y")
        new_value = new_value.strftime("%B %d, %Y")

    if event.value == "LIST" or event.value == "DETAILED":
        change = {
            "event": event.value,
            "event_message": (
                f"{changelog.changed_by.get_full_name()} "
                f"changed value of {field_display_name}"
            ),
            "changed_by": changelog.changed_by.get_full_name(),
            "timestamp": timestamp,
            "old_value": old_value,
            "new_value": new_value,
        }
    elif event.value == "BOOLEAN":
        change = {
            "event": event.value,
            "event_message": (
                f"{changelog.changed_by.get_full_name()} "
                f"set the {field_display_name} "
                f"as {new_value}"
            ),
            "changed_by": changelog.changed_by.get_full_name(),
            "timestamp": timestamp,
        }
    else:
        change = {
            "event": event.value,
            "event_message": (
                f"{changelog.changed_by.get_full_name()} "
                f"changed value of {field_display_name} from "
                f"{old_value} to {new_value}"
            ),
            "changed_by": changelog.changed_by.get_full_name(),
            "timestamp": timestamp,
        }

    return change
