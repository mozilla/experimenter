from rest_framework import serializers

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
)


class ExperimentVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentVariant
        fields = (
            'description',
            'name',
            'ratio',
            'slug',
            'value',
        )


class ExperimentSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    variant = ExperimentVariantSerializer()
    control = ExperimentVariantSerializer()

    class Meta:
        model = Experiment
        fields = (
            'accept_url',
            'client_matching',
            'control',
            'experiment_slug',
            'experiment_url',
            'firefox_channel',
            'firefox_version',
            'name',
            'objectives',
            'population_percent',
            'pref_branch',
            'pref_key',
            'pref_type',
            'project_name',
            'reject_url',
            'slug',
            'variant',
        )
