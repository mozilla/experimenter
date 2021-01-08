import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from parameterized import parameterized_class

from experimenter.experiments.models import NimbusExperiment, NimbusIsolationGroup
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusBucketRangeFactory,
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
    NimbusIsolationGroupFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperiment(TestCase):
    def test_str(self):
        experiment = NimbusExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(str(experiment), experiment.name)

    def test_targeting_config_not_set(self):
        experiment = NimbusExperimentFactory.create(
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING
        )
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

    def test_start_date_returns_None_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        self.assertIsNone(experiment.start_date)

    def test_end_date_returns_None_for_not_ended_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        self.assertIsNone(experiment.end_date)

    def test_start_date_returns_datetime_for_started_experiment(self):
        experiment = NimbusExperimentFactory.create()
        start_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.ACCEPTED,
            new_status=NimbusExperiment.Status.LIVE,
        )
        self.assertEqual(experiment.start_date, start_change.changed_on)

    def test_end_date_returns_datetime_for_ended_experiment(self):
        experiment = NimbusExperimentFactory.create()
        end_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        )
        self.assertEqual(experiment.end_date, end_change.changed_on)

    def test_proposed_end_date_returns_None_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        self.assertIsNone(experiment.proposed_end_date)

    def test_proposed_end_date_returns_start_date_plus_duration(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_duration=10,
        )
        self.assertEqual(
            experiment.proposed_end_date,
            datetime.date.today() + datetime.timedelta(days=10),
        )

    def test_should_end_returns_False_before_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_duration=10,
        )
        self.assertFalse(experiment.should_end)

    def test_should_end_returns_True_after_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_duration=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.ACCEPTED,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))
        self.assertTrue(experiment.should_end)

    def test_monitoring_dashboard_url_is_when_experiment_not_begun(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.DRAFT,
        )
        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.slug,
                from_date="",
                to_date="",
            ),
        )

    def test_monitoring_dashboard_url_returns_url_when_experiment_is_begun(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.LIVE,
        )

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.ACCEPTED,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.slug,
                from_date=1556582400000,
                to_date="",
            ),
        )

    def test_monitoring_dashboard_url_returns_url_when_experiment_is_complete(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.COMPLETE,
        )

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.ACCEPTED,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=datetime.date(2019, 5, 10),
        )

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.slug,
                from_date=1556582400000,
                to_date=1557619200000,
            ),
        )

    def test_clear_branches_deletes_branches_without_deleting_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        self.assertIsNotNone(experiment.reference_branch)
        self.assertEqual(experiment.branches.count(), 2)
        self.assertEqual(experiment.changes.count(), 1)

        experiment.delete_branches()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertIsNone(experiment.reference_branch)
        self.assertEqual(experiment.branches.count(), 0)
        self.assertEqual(experiment.changes.count(), 1)


class TestNimbusBranch(TestCase):
    def test_str(self):
        branch = NimbusBranchFactory.create()
        self.assertEqual(str(branch), branch.name)


@parameterized_class(
    ("application", "randomization_unit"),
    [
        [
            NimbusExperiment.Application.DESKTOP,
            NimbusExperiment.BucketRandomizationUnit.NORMANDY,
        ],
        [
            NimbusExperiment.Application.FENIX,
            NimbusExperiment.BucketRandomizationUnit.NIMBUS,
        ],
    ],
)
class TestNimbusIsolationGroup(TestCase):
    def test_empty_isolation_group_creates_isolation_group_and_bucket_range(self):
        """
        Common case: A new empty isolation group for an experiment
        that is orthogonal to all other current experiments.  This will
        likely describe most experiment launches.
        """
        experiment = NimbusExperimentFactory.create(application=self.application)
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
            self.randomization_unit,
        )

    def test_existing_isolation_group_adds_bucket_range(self):
        """
        Rare case: An isolation group with no buckets allocated already exists.
        This may become common when users can create their own isolation groups
        and then later assign experiments to them.
        """
        experiment = NimbusExperimentFactory.create(application=self.application)
        isolation_group = NimbusIsolationGroupFactory.create(
            name=experiment.slug, application=self.application
        )
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group, isolation_group)
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            self.randomization_unit,
        )

    def test_existing_isolation_group_with_buckets_adds_next_bucket_range(self):
        """
        Common case: An isolation group with experiment bucket allocations exists,
        and a subsequent bucket allocation is requested.  This will be the common case
        for any experiments that share an isolation group.
        """
        experiment = NimbusExperimentFactory.create(application=self.application)
        isolation_group = NimbusIsolationGroupFactory.create(
            name=experiment.slug, application=self.application
        )
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
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            self.randomization_unit,
        )

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
        experiment = NimbusExperimentFactory.create(application=self.application)
        isolation_group = NimbusIsolationGroupFactory.create(
            name=experiment.slug, application=self.application, total=100
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
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            self.randomization_unit,
        )

    def test_existing_isolation_group_with_matching_name_but_not_application_is_filtered(
        self,
    ):
        """
        Now that isolation groups are bound to applications, we have to check for the
        case where isolation groups with the same name but different applications are
        treated separately.
        """
        name = "isolation group name"
        NimbusIsolationGroupFactory.create(
            name=name, application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create(
            name=name, slug=name, application=NimbusExperiment.Application.FENIX
        )
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            name, experiment, 100
        )
        self.assertEqual(bucket.isolation_group.name, name)
        self.assertEqual(
            bucket.isolation_group.application, NimbusExperiment.Application.FENIX
        )


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
