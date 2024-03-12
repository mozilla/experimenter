import json

from django.test import TestCase

from experimenter.experiments.api.v5.serializers import (
    FmlFeatureValueSerializer,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.api.v5.test_serializers.mixins import (
    MockFmlErrorMixin,
)
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFmlErrorDataClass,
)


class TestFmlFeatureValueSerializer(MockFmlErrorMixin, TestCase):
    maxDiff = None

    def test_serializer_returns_fml_errors(self):
        self.setup_get_fml_errors(
            [
                NimbusFmlErrorDataClass(
                    line=1,
                    col=0,
                    message="Incorrect value!",
                    highlight="enabled",
                ),
            ]
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
        )
        data = {"featureSlug": "blerp", "featureValue": json.dumps({"some": "value"})}

        serializer = FmlFeatureValueSerializer(experiment, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(
            serializer.data,
            [
                {
                    "line": 1,
                    "col": 0,
                    "highlight": "enabled",
                    "message": "Incorrect value!",
                }
            ],
        )
