import datetime

from django.test import TestCase

from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.serializers import (
    JSTimestampField,
    ExperimentVariantSerializer,
    ExperimentSerializer,
)


class TestJSTimestampField(TestCase):

    def test_field_serializes_to_js_time_format(self):
        field = JSTimestampField()
        example_datetime = datetime.datetime(2000, 1, 1, 1, 1, 1, 1)
        self.assertEqual(
            field.to_representation(example_datetime), 946688461000.0)

    def test_field_returns_none_if_no_datetime_passed_in(self):
        field = JSTimestampField()
        self.assertEqual(field.to_representation(None), None)


class TestExperimentVariantSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        variant = ExperimentVariantFactory.create()
        serialized = ExperimentVariantSerializer(variant)
        self.assertEqual(serialized.data, {
            'slug': variant.slug,
            'experiment_variant_slug': variant.experiment_variant_slug,
            'ratio': variant.ratio,
            'value': variant.value,
        })


class TestExperimentSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_variants()
        serialized = ExperimentSerializer(experiment)
        self.assertEqual(serialized.data, {
            'name': experiment.name,
            'slug': experiment.slug,
            'firefox_version': experiment.firefox_version,
            'firefox_channel': experiment.firefox_channel,
            'objectives': experiment.objectives,
            'pref_key': experiment.pref_key,
            'pref_type': experiment.pref_type,
            'start_date': JSTimestampField().to_representation(
                experiment.start_date),
            'end_date': JSTimestampField().to_representation(
                experiment.end_date),
            'variant': ExperimentVariantSerializer(experiment.variant).data,
            'control': ExperimentVariantSerializer(experiment.control).data,
        })
