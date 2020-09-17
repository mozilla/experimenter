from django.test import TestCase

from experimenter.experiments.models import (
    NimbusBucketNamespace,
    NimbusExperiment,
)
from experimenter.experiments.tests.factories import (
    NimbusBucketNamespaceFactory,
    NimbusBucketRangeFactory,
    NimbusExperimentFactory,
)


class TestNimbusExperimentModel(TestCase):
    def test_str(self):
        experiment = NimbusExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(str(experiment), experiment.name)


class TestNimbusBucketNamespace(TestCase):
    def test_empty_namespace_creates_namespace_and_bucket_range(self):
        experiment = NimbusExperimentFactory.create()
        bucket = NimbusBucketNamespace.request_namespace_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.namespace.name, experiment.slug)
        self.assertEqual(bucket.namespace.instance, 1)
        self.assertEqual(bucket.namespace.total, NimbusExperiment.BUCKET_TOTAL)
        self.assertEqual(
            bucket.namespace.randomization_unit,
            NimbusExperiment.BUCKET_RANDOMIZATION_UNIT,
        )

    def test_existing_namespace_adds_bucket_range(self):
        experiment = NimbusExperimentFactory.create()
        namespace = NimbusBucketNamespaceFactory.create(name=experiment.slug)
        bucket = NimbusBucketNamespace.request_namespace_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.namespace, namespace)

    def test_existing_namespace_with_buckets_adds_next_bucket_range(self):
        experiment = NimbusExperimentFactory.create()
        namespace = NimbusBucketNamespaceFactory.create(name=experiment.slug)
        NimbusBucketRangeFactory.create(namespace=namespace, start=0, count=100)
        bucket = NimbusBucketNamespace.request_namespace_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 100)
        self.assertEqual(bucket.end, 199)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.namespace, namespace)

    def test_full_namespace_creates_next_namespace_instance_and_adds_bucket_range(self):
        experiment = NimbusExperimentFactory.create()
        namespace = NimbusBucketNamespaceFactory.create(name=experiment.slug, total=100)
        NimbusBucketRangeFactory(namespace=namespace, count=100)
        bucket = NimbusBucketNamespace.request_namespace_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.namespace.name, namespace.name)
        self.assertEqual(bucket.namespace.instance, namespace.instance + 1)
