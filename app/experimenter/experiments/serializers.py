import time

from rest_framework import serializers

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
)


class JSTimestampField(serializers.Field):
    """
    Serialize a datetime object into javascript timestamp
    ie unix time in ms
    """

    def to_representation(self, obj):
        if obj:
            return time.mktime(obj.timetuple()) * 1000
        else:
            return None


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
    control = ExperimentVariantSerializer()
    end_date = JSTimestampField()
    project_name = serializers.ReadOnlyField(source='project.name')
    start_date = JSTimestampField()
    variant = ExperimentVariantSerializer()

    class Meta:
        model = Experiment
        fields = (
            'accept_url',
            'client_matching',
            'control',
            'end_date',
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
            'start_date',
            'variant',
        )
