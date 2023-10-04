import json

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from rest_framework import serializers

from experimenter.experiments.constants import ChangeEventType, RelationalFields
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


# This method generates a formatted change dictionary based on the provided field name,
# field difference, changelog, and timestamp. It determines the event type based on the
# field type and generates an appropriate event message.

# Depending on the field type, the method may perform additional processing to obtain
# human-readable values for relational fields, JSON fields, and arrays.


def get_formatted_change_object(field_name, field_diff, changelog, timestamp):
    event_name = ChangeEventType.GENERAL.name
    field_instance = NimbusExperiment._meta.get_field(field_name)
    field_display_name = getattr(field_instance, "verbose_name", field_name)

    old_value = field_diff.get("old_value")
    new_value = field_diff.get("new_value")

    if isinstance(
        field_instance,
        (models.ManyToManyField, models.OneToOneField, models.ManyToOneRel),
    ):
        event_name = ChangeEventType.DETAILED.name

        # Values of some fields are stored in the form of reference keys in
        # NimbusChangeLog and the NATIVE_MODELS here is a list of the
        # database models to which those fields belong to. We use this list
        # to query the actual values of those fields using the reference keys

        if field_name in RelationalFields.NATIVE_MODELS:
            field_model = field_instance.related_model
            data = field_model.objects.all()
            if old_value is not None:
                values = list(
                    data.filter(pk__in=old_value).values_list("name", flat=True)
                )
                old_value = values
            else:
                old_value = []

            values = list(data.filter(pk__in=new_value).values_list("name", flat=True))
            new_value = values

        old_value = json.dumps(old_value, indent=2)
        new_value = json.dumps(new_value, indent=2)

    elif isinstance(field_instance, (models.JSONField, ArrayField)):
        event_name = ChangeEventType.DETAILED.name
        if old_value is not None:
            old_value = json.dumps(old_value, indent=2)
        if new_value is not None:
            new_value = json.dumps(new_value, indent=2)

    elif isinstance(field_instance, models.BooleanField):
        event_name = ChangeEventType.BOOLEAN.name

    if field_name == "status" or field_name == "publish_status":
        event_name = ChangeEventType.STATE.name

    if event_name == ChangeEventType.DETAILED.name:
        change_message = f"{changelog.changed_by} changed value of {field_display_name}"
    elif event_name == ChangeEventType.BOOLEAN.name:
        change_message = (
            f"{changelog.changed_by} set the {field_display_name} as {new_value}"
        )
    else:
        change_message = (
            f"{changelog.changed_by} changed value of {field_display_name} from "
            f"{old_value} to {new_value}"
        )

    return {
        "event": event_name,
        "event_message": change_message,
        "changed_by": changelog.changed_by,
        "timestamp": timestamp,
        "old_value": old_value,
        "new_value": new_value,
    }
