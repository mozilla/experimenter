from django.utils.text import slugify
from rest_framework import serializers

from experimenter.bugzilla.tasks import create_experiment_bug_task
from experimenter.experiments.models import Experiment
from experimenter.experiments.changelog_utils import ChangelogSerializerMixin


class ExperimentRapidSerializer(ChangelogSerializerMixin, serializers.ModelSerializer):
    type = serializers.HiddenField(default=Experiment.TYPE_RAPID)
    rapid_type = serializers.HiddenField(default=Experiment.RAPID_AA_CFR)
    owner = serializers.ReadOnlyField(source="owner.email")
    slug = serializers.ReadOnlyField()
    public_description = serializers.HiddenField(
        default=Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE
    )
    objectives = serializers.CharField(required=True)
    features = serializers.ListField(
        required=True,
        child=serializers.ChoiceField(choices=Experiment.RAPID_FEATURE_CHOICES),
        allow_empty=False,
    )
    audience = serializers.ChoiceField(
        required=True, choices=Experiment.RAPID_AUDIENCE_CHOICES
    )
    bugzilla_url = serializers.ReadOnlyField()

    class Meta:
        model = Experiment
        fields = (
            "type",
            "rapid_type",
            "owner",
            "name",
            "slug",
            "objectives",
            "public_description",
            "features",
            "audience",
            "bugzilla_url",
        )

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
        return validated_data

    def create(self, validated_data):
        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
                "owner": self.context["request"].user,
            }
        )
        experiment = super().create(validated_data)
        self.update_changelog(experiment, validated_data)
        create_experiment_bug_task.delay(experiment.owner.id, experiment.id)
        return experiment

    def update(self, instance, validated_data):
        updated_instance = super().update(instance, validated_data)
        self.update_changelog(updated_instance, validated_data)
        return updated_instance
