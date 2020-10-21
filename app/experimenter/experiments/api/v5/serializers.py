from rest_framework import serializers

from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.models import NimbusExperiment


class NimbusChangeLogMixin:
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        generate_nimbus_changelog(experiment, self.context["user"])
        return experiment


class NimbusExperimentSerializer(NimbusChangeLogMixin, serializers.ModelSerializer):
    class Meta:
        model = NimbusExperiment
        fields = ("name", "slug", "application", "public_description", "hypothesis")
