from django.test import TestCase

from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.serializers import (
    ExperimentVariantSerializer,
    ExperimentSerializer,
)


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
            'project_name': experiment.project.name,
            'name': experiment.name,
            'slug': experiment.slug,
            'experiment_slug': experiment.experiment_slug,
            'firefox_version': experiment.firefox_version,
            'firefox_channel': experiment.firefox_channel,
            'population_percent': '{0:.4f}'.format(
                experiment.population_percent),
            'objectives': experiment.objectives,
            'pref_key': experiment.pref_key,
            'pref_type': experiment.pref_type,
            'variant': ExperimentVariantSerializer(experiment.variant).data,
            'control': ExperimentVariantSerializer(experiment.control).data,
        })
