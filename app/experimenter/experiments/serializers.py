from rest_framework import serializers

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
)


class ExperimentVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentVariant
        fields = (
            'slug',
            'experiment_variant_slug',
            'value',
            'ratio',
        )


class ExperimentSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    variant = ExperimentVariantSerializer()
    control = ExperimentVariantSerializer()

    class Meta:
        model = Experiment
        fields = (
            'project_name',
            'name',
            'slug',
            'experiment_slug',
            'firefox_version',
            'firefox_channel',
            'objectives',
            'pref_key',
            'pref_type',
            'variant',
            'control',
        )
