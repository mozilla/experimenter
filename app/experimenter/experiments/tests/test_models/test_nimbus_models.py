from django.test import TestCase
from django.utils import timezone

from experimenter.experiments.models import NimbusExperiment, NimbusIsolationGroup
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusBucketRangeFactory,
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
    NimbusIsolationGroupFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentModel(TestCase):
    def test_str(self):
        experiment = NimbusExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(str(experiment), experiment.name)

    def test_targeting_config_not_set(self):
        experiment = NimbusExperimentFactory.create(targeting_config_slug=None)
        self.assertIsNone(experiment.targeting_config)

    def test_targeting_config_set(self):
        experiment = NimbusExperimentFactory.create(
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH
        )
        self.assertEqual(
            experiment.targeting_config,
            NimbusExperiment.TARGETING_CONFIGS[
                NimbusExperiment.TargetingConfig.ALL_ENGLISH
            ],
        )


class TestNimbusBranchModel(TestCase):
    def test_str(self):
        branch = NimbusBranchFactory.create()
        self.assertEqual(str(branch), branch.name)


class TestNimbusIsolationGroup(TestCase):
    def test_empty_isolation_group_creates_isolation_group_and_bucket_range(self):
        """
        Common case: A new empty isolation group for an experiment
        that is orthogonal to all other current experiments.  This will
        likely describe most experiment launches.
        """
        experiment = NimbusExperimentFactory.create()
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group.name, experiment.slug)
        self.assertEqual(bucket.isolation_group.instance, 1)
        self.assertEqual(bucket.isolation_group.total, NimbusExperiment.BUCKET_TOTAL)
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            NimbusExperiment.BUCKET_RANDOMIZATION_UNIT,
        )

    def test_existing_isolation_group_adds_bucket_range(self):
        """
        Rare case: An isolation group with no buckets allocated already exists.
        This may become common when users can create their own isolation groups
        and then later assign experiments to them.
        """
        experiment = NimbusExperimentFactory.create()
        isolation_group = NimbusIsolationGroupFactory.create(name=experiment.slug)
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group, isolation_group)

    def test_existing_isolation_group_with_buckets_adds_next_bucket_range(self):
        """
        Common case: An isolation group with experiment bucket allocations exists,
        and a subsequent bucket allocation is requested.  This will be the common case
        for any experiments that share an isolation group.
        """
        experiment = NimbusExperimentFactory.create()
        isolation_group = NimbusIsolationGroupFactory.create(name=experiment.slug)
        NimbusBucketRangeFactory.create(
            isolation_group=isolation_group, start=0, count=100
        )
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 100)
        self.assertEqual(bucket.end, 199)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group, isolation_group)

    def test_full_isolation_group_creates_next_isolation_group_adds_bucket_range(
        self,
    ):
        """
        Rare case:  An isolation group with experiment bucket allocations exists, and the
        next requested bucket allocation would overflow its total bucket range, and so a
        an isolation group with the same name but subsequent instance ID is created.

        This is currently treated naively, ie does not account for possible collisions and
        overlaps.  When this case becomes more common this will likely need to be given
        more thought.
        """
        experiment = NimbusExperimentFactory.create()
        isolation_group = NimbusIsolationGroupFactory.create(
            name=experiment.slug, total=100
        )
        NimbusBucketRangeFactory(isolation_group=isolation_group, count=100)
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group.name, isolation_group.name)
        self.assertEqual(bucket.isolation_group.instance, isolation_group.instance + 1)


class TestNimbusChangeLog(TestCase):
    def test_uses_message_if_set(self):
        changelog = NimbusChangeLogFactory.create()
        self.assertEqual(str(changelog), changelog.message)

    def test_formats_str_if_no_message_set(self):
        now = timezone.now()
        user = UserFactory.create()
        changelog = NimbusChangeLogFactory.create(
            changed_by=user,
            changed_on=now,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.REVIEW,
            message=None,
        )
        self.assertEqual(str(changelog), f"Draft > Review by {user.email} on {now}")
