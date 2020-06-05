from django.utils.text import slugify
from rest_framework import serializers

from experimenter.experiments.models import Experiment


class ExperimentRapidSerializer(serializers.ModelSerializer):
    type = serializers.HiddenField(default=Experiment.TYPE_RAPID)
    rapid_type = serializers.HiddenField(default=Experiment.RAPID_AA_CFR)
    owner = serializers.ReadOnlyField(source="owner.email")
    slug = serializers.ReadOnlyField()

    class Meta:
        model = Experiment
        fields = (
            "type",
            "rapid_type",
            "owner",
            "name",
            "slug",
            "objectives",
        )

    def create(self, validated_data):
        experiment = super().create(validated_data)
        experiment.slug = slugify(experiment.name)
        experiment.owner = self.context["request"].user
        experiment.save()
        return experiment
