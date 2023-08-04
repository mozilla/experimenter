from experimenter.experiments.constants import NimbusConstants
from django.db import models
from django.contrib.postgres.fields import ArrayField

def get_change_object(field_name, field_diff, changelog, timestamp):
    event = NimbusConstants.ChangeEvent.find_enum_by_key(field_name.upper())
    field_display_name = (
        event.display_name
        if event.value != NimbusConstants.ChangeEvent.GENERAL.value
        else field_name
    )

    old_value = field_diff['old_value']
    new_value = field_diff['new_value']

    if isinstance(old_value, models.ManyToManyField) or isinstance(old_value, ArrayField):
        message = (
            f"{changelog.changed_by.get_full_name()} "
            f"changed value of {field_display_name}"
        )
    elif isinstance(old_value, models.JSONField):
        change = {
            "event": event.value,
            "event_message": (
                f"{changelog.changed_by.get_full_name()} "
                f"changed value of {field_display_name}"
            ),
            "changed_by": changelog.changed_by.get_full_name(),
            "timestamp": timestamp,
            "old_value": old_value,
            "new_value": new_value
        }
        return change
    else:
        message = (
            f"{changelog.changed_by.get_full_name()} "
            f"changed value of {field_display_name} from "
            f"{old_value} to {new_value}"
        )

    change = {
        "event": event.value,
        "event_message": message,
        "changed_by": changelog.changed_by.get_full_name(),
        "timestamp": timestamp,
    }
    return change
