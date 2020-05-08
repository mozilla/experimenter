from django.contrib.auth import get_user_model
from django.conf import settings

from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.serializers.entities import ChangeLogSerializer


def update_experiment_with_change_log(experiment, changed_data):

    old_serialized_exp = ChangeLogSerializer(experiment).data
    Experiment.objects.filter(id=experiment.id).update(**changed_data)
    experiment = Experiment.objects.get(slug=experiment.slug)
    new_serialized_exp = ChangeLogSerializer(experiment).data
    normandy_user = settings.NORMANDY_DEFAULT_CHANGELOG_USER
    default_user, _ = get_user_model().objects.get_or_create(
        email=normandy_user, username=normandy_user
    )

    generate_change_log(
        old_serialized_exp, new_serialized_exp, experiment, changed_data, default_user,
    )


def generate_change_log(
    old_serialized_vals,
    new_serialized_vals,
    instance,
    changed_data,
    user,
    message=None,
    form_fields=None,
):
    changed_values = {}
    old_status = None

    latest_change = instance.changes.latest()

    # account for changes in variant values
    if latest_change:
        old_status = latest_change.new_status
        if old_serialized_vals["variants"] != new_serialized_vals["variants"]:
            old_value = old_serialized_vals["variants"]
            new_value = new_serialized_vals["variants"]
            display_name = "Branches"
            changed_values["variants"] = {
                "old_value": old_value,
                "new_value": new_value,
                "display_name": display_name,
            }

    elif new_serialized_vals.get("variants"):
        old_value = None
        new_value = new_serialized_vals["variants"]
        display_name = "Branches"
        changed_values["variants"] = {
            "old_value": old_value,
            "new_value": new_value,
            "display_name": display_name,
        }

    if changed_data:
        if latest_change:
            old_status = latest_change.new_status

            for field in changed_data:
                old_val = None
                new_val = None

                if field in old_serialized_vals:
                    if field in ("countries", "locales"):
                        old_field_values = old_serialized_vals[field]
                        codes = [obj["code"] for obj in old_field_values]
                        old_val = codes
                    else:
                        old_val = old_serialized_vals[field]
                if field in new_serialized_vals:
                    if field in ("countries", "locales"):
                        new_field_values = new_serialized_vals[field]
                        codes = [obj["code"] for obj in new_field_values]
                        new_val = codes
                    else:
                        new_val = new_serialized_vals[field]

                display_name = _get_display_name(field, form_fields)

                if new_val != old_val:
                    changed_values[field] = {
                        "old_value": old_val,
                        "new_value": new_val,
                        "display_name": display_name,
                    }

        else:
            for field in changed_data:
                old_val = None
                new_val = None
                if field in new_serialized_vals:
                    if field in ("countries", "locales"):
                        new_field_values = new_serialized_vals[field]
                        codes = [obj["code"] for obj in new_field_values]
                        new_val = codes
                    else:
                        new_val = new_serialized_vals[field]
                    display_name = _get_display_name(field, form_fields)
                    changed_values[field] = {
                        "old_value": old_val,
                        "new_value": new_val,
                        "display_name": display_name,
                    }
    if _has_changed(old_status, changed_values, instance, message):
        ExperimentChangeLog.objects.create(
            experiment=instance,
            changed_by=user,
            old_status=old_status,
            new_status=instance.status,
            changed_values=changed_values,
            message=message,
        )


def _has_changed(old_status, changed_values, experiment, message):
    return changed_values or message or old_status != experiment.status


def _get_display_name(field, form_fields):
    if form_fields and form_fields[field].label:
        return form_fields[field].label
    return field.replace("_", " ").title()
