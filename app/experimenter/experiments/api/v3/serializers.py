from django.utils.text import slugify
from rest_framework import serializers

from mozilla_nimbus_shared import get_data

from experimenter.bugzilla.tasks import create_experiment_bug_task
from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
)
from experimenter.experiments.changelog_utils import ChangelogSerializerMixin


NIMBUS_DATA = get_data()


class ExperimentRapidRejectChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentChangeLog
        fields = ("message", "changed_on")


class ExperimentRapidChangelogSerializerMixin(ChangelogSerializerMixin):
    def create(self, validated_data):
        experiment = super().create(validated_data)
        self.update_changelog(experiment, validated_data)
        return experiment

    def update(self, instance, validated_data):
        updated_instance = super().update(instance, validated_data)
        self.update_changelog(updated_instance, validated_data)
        return updated_instance


class ExperimentRapidVariantSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField()

    def validate_ratio(self, value):
        if 1 <= value <= 100:
            return value

        raise serializers.ValidationError(["Branch sizes must be between 1 and 100."])

    class Meta:
        fields = ["slug", "name", "description", "is_control", "ratio", "value"]
        model = ExperimentVariant


class ExperimentRapidSerializer(
    ExperimentRapidChangelogSerializerMixin, serializers.ModelSerializer
):
    FEATURES_CHOICES = list(NIMBUS_DATA["features"].keys())
    AUDIENCE_CHOICES = list(NIMBUS_DATA["Audiences"].keys())

    type = serializers.HiddenField(default=Experiment.TYPE_RAPID)
    rapid_type = serializers.HiddenField(default=Experiment.RAPID_AA)
    owner = serializers.ReadOnlyField(source="owner.email")
    slug = serializers.ReadOnlyField()
    public_description = serializers.HiddenField(
        default=Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE
    )
    objectives = serializers.CharField(required=True)
    features = serializers.ListField(
        required=True,
        child=serializers.ChoiceField(choices=FEATURES_CHOICES),
        allow_empty=False,
    )
    audience = serializers.ChoiceField(required=True, choices=AUDIENCE_CHOICES)
    bugzilla_url = serializers.ReadOnlyField()
    firefox_min_version = serializers.ChoiceField(
        required=True, choices=Experiment.VERSION_CHOICES,
    )
    firefox_channel = serializers.ChoiceField(
        required=True, choices=Experiment.CHANNEL_CHOICES
    )
    monitoring_dashboard_url = serializers.ReadOnlyField()
    reject_feedback = serializers.SerializerMethodField()

    variants = ExperimentRapidVariantSerializer(many=True)

    class Meta:
        model = Experiment
        fields = (
            "audience",
            "bugzilla_url",
            "features",
            "firefox_min_version",
            "firefox_channel",
            "monitoring_dashboard_url",
            "name",
            "objectives",
            "owner",
            "public_description",
            "rapid_type",
            "slug",
            "status",
            "type",
            "reject_feedback",
            "recipe_slug",
            "variants",
        )

    def get_reject_feedback(self, obj):
        if obj.status == Experiment.STATUS_REJECTED:
            return ExperimentRapidRejectChangeLogSerializer(obj.changes.latest()).data

    def validate(self, data):
        validated_data = super().validate(data)
        if validated_data.get("slug") is None:
            slug = slugify(data.get("name"))

            if not slug:
                raise serializers.ValidationError(
                    {"name": ["Name needs to contain alphanumeric characters"]}
                )
            if (
                self.instance is None
                and slug
                and Experiment.objects.filter(slug=slug).exists()
            ):
                raise serializers.ValidationError(
                    {
                        "name": [
                            "Name maps to a pre-existing slug, please choose another name"
                        ]
                    }
                )

        variants = data.get("variants")

        if variants:
            if not self.all_variant_slugs_unique(variants):
                error_list = []
                for variant in variants:
                    error_list.append(
                        {"name": [("All branches must have a unique name")]}
                    )

                raise serializers.ValidationError({"variants": error_list})

        return validated_data

    def all_variant_slugs_unique(self, variants):

        slugified_names = [slugify(variant["name"]) for variant in variants]
        unique_names = len(set(slugified_names)) == len(variants)
        non_empty = all(slugified_names)

        return unique_names and non_empty

    def create(self, validated_data):
        preset_data = NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"][
            "arguments"
        ].copy()

        variants_validated = validated_data.pop("variants")

        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
                "owner": self.context["request"].user,
                "proposed_duration": preset_data["proposedDuration"],
                "proposed_enrollment": preset_data["proposedEnrollment"],
            }
        )
        experiment = super().create(validated_data)

        for v in variants_validated:
            v["experiment"] = experiment
            v["slug"] = slugify(v["name"])

        self.fields["variants"].create(variants_validated)

        create_experiment_bug_task.delay(experiment.owner.id, experiment.id)
        return experiment

    def update(self, instance, validated_data):
        # TODO: Update branches
        validated_data.pop("variants")

        instance = super().update(instance, validated_data)

        return instance


class ExperimentRapidStatusSerializer(
    ExperimentRapidChangelogSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = Experiment
        fields = ("status",)

    def validate_status(self, status):
        expected_status = (
            self.instance.status in self.instance.RAPID_STATUS_TRANSITIONS
            and status in self.instance.RAPID_STATUS_TRANSITIONS[self.instance.status]
        )

        if not expected_status:
            raise serializers.ValidationError(
                (
                    "You can not change an experiment's status "
                    f"from {self.instance.status} to {status}"
                )
            )

        return status
