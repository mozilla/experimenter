import time

from rest_framework import serializers

from experimenter.experiments.models import Experiment, ExperimentVariant


class JSTimestampField(serializers.Field):
    """
    Serialize a datetime object into javascript timestamp
    ie unix time in ms
    """

    def to_representation(self, obj):
        return time.mktime(obj.timetuple()) * 1000


class ExperimentVariantSerializer(serializers.ModelSerializer):
    threshold = serializers.FloatField()

    class Meta:
        model = ExperimentVariant
        fields = (
            'slug',
            'experiment_variant_slug',
            'value',
            'threshold',
        )


class ExperimentControlSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentVariant
        fields = (
            'slug',
            'experiment_variant_slug',
            'value',
        )


class ExperimentSerializer(serializers.ModelSerializer):
    start_date = JSTimestampField()
    end_date = JSTimestampField()
    variant = ExperimentVariantSerializer()
    control = ExperimentControlSerializer()

    class Meta:
        model = Experiment
        fields = (
            'name',
            'slug',
            'active',
            'start_date',
            'end_date',
            'variant',
            'control',
        )
