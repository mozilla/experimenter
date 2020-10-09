from rest_framework import serializers

from experimenter.experiments.models import NimbusExperiment


class NimbusExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusExperiment
        fields = ("name", "slug", "application", "public_description", "hypothesis")
