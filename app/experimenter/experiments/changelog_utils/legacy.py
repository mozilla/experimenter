from django.contrib.auth import get_user_model
from rest_framework import serializers

from experimenter.base.serializers import CountrySerializer, LocaleSerializer
from experimenter.experiments.api.v1.serializers import (
    ExperimentRolloutPreferenceSerializer,
    ExperimentVariantSerializer,
)
from experimenter.experiments.email import send_experiment_change_email
from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.projects.serializers import ProjectSerializer


class ChangelogSerializerMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_serialized_vals = {}
        if self.instance and self.instance.id:
            self.old_serialized_vals = ChangeLogSerializer(self.instance).data

    def update_changelog(self, instance, validated_data):
        new_serialized_vals = ChangeLogSerializer(instance).data
        user = self.context["request"].user
        changed_data = validated_data.copy()
        generate_change_log(
            self.old_serialized_vals, new_serialized_vals, instance, changed_data, user
        )

        return instance


class ChangeLogSerializer(serializers.ModelSerializer):
    variants = ExperimentVariantSerializer(many=True, required=False)
    locales = LocaleSerializer(many=True, required=False)
    countries = CountrySerializer(many=True, required=False)
    projects = ProjectSerializer(many=True, required=False)
    preferences = ExperimentRolloutPreferenceSerializer(many=True, required=False)

    class Meta:
        model = Experiment
        fields = (
            "type",
            "owner",
            "name",
            "short_description",
            "related_work",
            "related_to",
            "proposed_start_date",
            "proposed_duration",
            "proposed_enrollment",
            "design",
            "addon_experiment_id",
            "addon_release_url",
            "pref_name",
            "pref_type",
            "pref_branch",
            "public_description",
            "population_percent",
            "firefox_min_version",
            "firefox_max_version",
            "firefox_channel",
            "client_matching",
            "locales",
            "countries",
            "projects",
            "platforms",
            "windows_versions",
            "profile_age",
            "objectives",
            "total_enrolled_clients",
            "analysis",
            "analysis_owner",
            "survey_required",
            "survey_urls",
            "survey_instructions",
            "engineering_owner",
            "bugzilla_id",
            "recipe_slug",
            "normandy_id",
            "other_normandy_ids",
            "data_science_issue_url",
            "feature_bugzilla_url",
            "risk_partner_related",
            "risk_brand",
            "risk_fast_shipped",
            "risk_confidential",
            "risk_release_population",
            "risk_revenue",
            "risk_data_category",
            "risk_external_team_impact",
            "risk_telemetry_data",
            "risk_ux",
            "risk_security",
            "risk_revision",
            "risk_technical",
            "risk_technical_description",
            "risks",
            "testing",
            "test_builds",
            "qa_status",
            "review_science",
            "review_engineering",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_bugzilla",
            "review_qa",
            "review_relman",
            "review_advisory",
            "review_legal",
            "review_ux",
            "review_security",
            "review_vp",
            "review_data_steward",
            "review_comms",
            "review_impacted_teams",
            "variants",
            "results_url",
            "results_initial",
            "results_lessons_learned",
            "results_fail_to_launch",
            "results_recipe_errors",
            "results_restarts",
            "results_low_enrollment",
            "results_early_end",
            "results_no_usable_data",
            "results_failures_notes",
            "results_changes_to_firefox",
            "results_data_for_hypothesis",
            "results_confidence",
            "results_measure_impact",
            "results_impact_notes",
            "rollout_type",
            "rollout_playbook",
            "message_type",
            "message_template",
            "preferences",
        )


def update_experiment_with_change_log(
    old_experiment, changed_data, user_email, message=None
):
    old_serialized_exp = ChangeLogSerializer(old_experiment).data
    Experiment.objects.filter(id=old_experiment.id).update(**changed_data)
    new_experiment = Experiment.objects.get(slug=old_experiment.slug)
    new_serialized_exp = ChangeLogSerializer(new_experiment).data

    default_user, _ = get_user_model().objects.get_or_create(
        email=user_email, username=user_email
    )

    generate_change_log(
        old_serialized_exp,
        new_serialized_exp,
        new_experiment,
        changed_data,
        default_user,
        message,
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
        change = ExperimentChangeLog.objects.create(
            experiment=instance,
            changed_by=user,
            old_status=old_status,
            new_status=instance.status,
            changed_values=changed_values,
            message=message,
        )
        send_experiment_change_email(change)


def _has_changed(old_status, changed_values, experiment, message):
    return changed_values or message or old_status != experiment.status


def _get_display_name(field, form_fields):
    if form_fields and form_fields[field].label:
        return form_fields[field].label
    return field.replace("_", " ").title()
