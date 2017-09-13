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
            'description': variant.description,
            'name': variant.name,
            'ratio': variant.ratio,
            'slug': variant.slug,
            'value': variant.value,
        })


class TestExperimentSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_variants()
        serialized = ExperimentSerializer(experiment)
        expected_data = {
            'accept_url': experiment.accept_url,
            'client_matching': experiment.client_matching,
            'control': ExperimentVariantSerializer(experiment.control).data,
            'experiment_slug': experiment.experiment_slug,
            'experiment_url': experiment.experiment_url,
            'firefox_channel': experiment.firefox_channel,
            'firefox_version': experiment.firefox_version,
            'name': experiment.name,
            'objectives': experiment.objectives,
            'population_percent': '{0:.4f}'.format(
                experiment.population_percent),
            'pref_branch': experiment.pref_branch,
            'pref_key': experiment.pref_key,
            'pref_type': experiment.pref_type,
            'project_name': experiment.project.name,
            'reject_url': experiment.reject_url,
            'slug': experiment.slug,
            'variant': ExperimentVariantSerializer(experiment.variant).data,
        }

        self.assertEqual(
            set(serialized.data.keys()), set(expected_data.keys()))
        self.assertEqual(serialized.data, expected_data)
