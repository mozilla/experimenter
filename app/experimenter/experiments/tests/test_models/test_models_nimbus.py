import datetime
from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from django.test import TestCase, override_settings
from django.utils import timezone
from parameterized import parameterized_class
from parameterized.parameterized import parameterized

from experimenter.experiments.changelog_utils.nimbus import generate_nimbus_changelog
from experimenter.experiments.models import NimbusExperiment, NimbusIsolationGroup
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusBucketRangeFactory,
    NimbusChangeLogFactory,
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
    NimbusIsolationGroupFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentManager(TestCase):
    def test_launch_queue_returns_queued_experiments_with_correct_application(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.FENIX,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertEqual(
            list(
                NimbusExperiment.objects.launch_queue(
                    [NimbusExperiment.Application.DESKTOP]
                )
            ),
            [experiment1],
        )

    def test_end_queue_returns_ending_experiments_with_correct_application(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_end_requested=True,
            application=NimbusExperiment.Application.FENIX,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.ENDING_APPROVE_REJECT,
            application=NimbusExperiment.Application.DESKTOP,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE,
            is_end_requested=True,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertEqual(
            list(
                NimbusExperiment.objects.end_queue([NimbusExperiment.Application.DESKTOP])
            ),
            [experiment1],
        )

    def test_pause_queue_returns_experiments_that_should_pause_by_application(self):
        def rewind_launch(experiment):
            launch_change = experiment.changes.get(
                old_status=NimbusExperiment.Status.DRAFT,
                new_status=NimbusExperiment.Status.LIVE,
            )
            launch_change.changed_on = datetime.datetime.now() - datetime.timedelta(
                days=11
            )
            launch_change.save()

        # Should end, with the correct application
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_paused=False,
            proposed_enrollment=10,
            application=NimbusExperiment.Application.DESKTOP,
        )
        rewind_launch(experiment1)
        # Should end, but wrong application
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            application=NimbusExperiment.Application.FENIX,
        )
        rewind_launch(experiment2)
        # Should end, but already paused
        experiment3 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_paused=True,
            proposed_enrollment=10,
            application=NimbusExperiment.Application.DESKTOP,
        )
        rewind_launch(experiment3)
        # Correct application, but should not end
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertEqual(
            list(
                NimbusExperiment.objects.pause_queue(
                    [NimbusExperiment.Application.DESKTOP]
                )
            ),
            [experiment1],
        )

    def test_waiting_returns_any_waiting_experiments(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            application=NimbusExperiment.Application.IOS,
        )
        desktop_live_waiting = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertEqual(
            list(
                NimbusExperiment.objects.waiting([NimbusExperiment.Application.DESKTOP])
            ),
            [desktop_live_waiting],
        )

    def test_waiting_to_launch_only_returns_launching_experiments(self):
        launching = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_WAITING
        )
        NimbusExperimentFactory.create_with_lifecycle(NimbusExperiment.Lifecycles.CREATED)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.ENDING_APPROVE_WAITING,
        )

        self.assertEqual(
            list(NimbusExperiment.objects.waiting_to_launch_queue()), [launching]
        )


class TestNimbusExperiment(TestCase):
    def test_str(self):
        experiment = NimbusExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(str(experiment), experiment.name)

    def test_targeting_for_experiment_without_channels(self):
        experiment = NimbusExperimentFactory.create(
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )

        self.assertEqual(
            experiment.targeting,
            (
                "version|versionCompare('83.!') >= 0 "
                "&& 'app.shield.optoutstudies.enabled'|preferenceValue "
                "&& localeLanguageCode == 'en'"
            ),
        )

    def test_targeting_for_mobile(self):
        experiment = NimbusExperimentFactory.create(
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )

        self.assertEqual(experiment.targeting, "localeLanguageCode == 'en'")

    def test_empty_targeting_for_mobile(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )

        self.assertEqual(experiment.targeting, "true")

    def test_targeting_without_firefox_min_version(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NIGHTLY,
        )

        self.assertEqual(
            experiment.targeting,
            (
                'browserSettings.update.channel == "nightly" '
                "&& 'app.shield.optoutstudies.enabled'|preferenceValue "
                "&& localeLanguageCode == 'en'"
            ),
        )

    def test_targeting_without_channel_version(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )
        self.assertEqual(
            experiment.targeting,
            "'app.shield.optoutstudies.enabled'|preferenceValue",
        )

    def test_start_date_returns_None_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.start_date)

    def test_end_date_returns_None_for_not_ended_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.end_date)

    def test_start_date_returns_datetime_for_started_experiment(self):
        experiment = NimbusExperimentFactory.create()
        start_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.proposed_end_date)

    def test_proposed_end_date_returns_start_date_plus_duration(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
        )
        self.assertEqual(
            experiment.proposed_end_date,
            datetime.date.today() + datetime.timedelta(days=10),
        )

    def test_should_end_returns_False_before_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
        )
        self.assertFalse(experiment.should_end)

    def test_should_end_returns_True_after_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
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

    def test_monitoring_dashboard_url_returns_url_when_experiment_has_begun(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.LIVE,
        )

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
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
            old_status=NimbusExperiment.Status.DRAFT,
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        self.assertIsNotNone(experiment.reference_branch)
        self.assertEqual(experiment.branches.count(), 2)
        self.assertEqual(experiment.changes.count(), 1)

        experiment.delete_branches()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertIsNone(experiment.reference_branch)
        self.assertEqual(experiment.branches.count(), 0)
        self.assertEqual(experiment.changes.count(), 1)

    def test_allocate_buckets_generates_bucket_range(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED, population_percent=Decimal("50.0")
        )
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 5000)
        self.assertEqual(
            experiment.bucket_range.isolation_group.name, experiment.feature_config.slug
        )

    def test_allocate_buckets_creates_new_bucket_range_if_population_changes(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED, population_percent=Decimal("50.0")
        )
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 5000)
        self.assertEqual(
            experiment.bucket_range.isolation_group.name, experiment.feature_config.slug
        )

        experiment.population_percent = Decimal("20.0")
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 2000)
        self.assertEqual(
            experiment.bucket_range.isolation_group.name, experiment.feature_config.slug
        )

    def test_proposed_enrollment_end_date_without_start_date_is_None(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.proposed_enrollment_end_date)

    def test_proposed_enrollment_end_date_with_start_date_returns_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE, proposed_enrollment=10
        )
        self.assertEqual(
            experiment.proposed_enrollment_end_date,
            datetime.date.today() + datetime.timedelta(days=10),
        )

    def test_should_pause_false_before_enrollment_end(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE, proposed_enrollment=10
        )
        self.assertFalse(experiment.should_pause)

    def test_should_pause_true_after_enrollment_end(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE, proposed_enrollment=10
        )
        launch_change = experiment.changes.get(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        )
        launch_change.changed_on = datetime.datetime.now() - datetime.timedelta(days=11)
        launch_change.save()
        self.assertTrue(experiment.should_pause)

    def test_can_review_false_for_requesting_user(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertFalse(experiment.can_review(experiment.owner))

    @parameterized.expand(
        (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
        )
    )
    def test_can_review_true_for_non_requesting_user(self, last_publish_status):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            generate_nimbus_changelog(experiment, experiment.owner, "test message")
            if publish_status == last_publish_status:
                break

        self.assertTrue(experiment.can_review(UserFactory.create()))

    def test_results_ready_true(self):
        experiment = NimbusExperimentFactory.create()

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )
        self.assertTrue(experiment.results_ready)

    def test_results_ready_false(self):
        experiment = NimbusExperimentFactory.create()

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date.today() - datetime.timedelta(days=2),
        )
        self.assertFalse(experiment.results_ready)

    @parameterized.expand([(settings.DEV_USER_EMAIL, True), ("jdoe@mozilla.org", False)])
    @override_settings(SKIP_REVIEW_ACCESS_CONTROL_FOR_DEV_USER=True)
    def test_can_review_for_requesting_user_if_dev_user_and_setting_enabled(
        self, email, is_allowed
    ):
        user = UserFactory.create(email=email)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            owner=user,
        )
        experiment.apply_lifecycle_state(NimbusExperiment.LifecycleStates.DRAFT_REVIEW)
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertEqual(experiment.can_review(user), is_allowed)

    def test_can_review_false_for_non_review_publish_status(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        experiment.apply_lifecycle_state(NimbusExperiment.LifecycleStates.DRAFT_REVIEW)
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE

        experiment.save()

        self.assertFalse(experiment.can_review(UserFactory.create()))

    @parameterized.expand(
        [
            (
                NimbusExperiment.Lifecycles.LAUNCH_APPROVE,
                NimbusExperiment.Lifecycles.LAUNCH_APPROVE_WAITING,
                NimbusExperiment.Lifecycles.LAUNCH_APPROVE_TIMEOUT,
            ),
            (
                NimbusExperiment.Lifecycles.ENDING_APPROVE,
                NimbusExperiment.Lifecycles.ENDING_APPROVE_WAITING,
                NimbusExperiment.Lifecycles.ENDING_APPROVE_TIMEOUT,
            ),
        ]
    )
    def test_timeout_changelog_for_timedout_publish_flow(
        self, lifecycle_start, lifecycle_waiting, lifecycle_timeout
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle_start)

        # Simulate waiting for approval in remote settings
        experiment.apply_lifecycle_state(lifecycle_waiting.value[-1])
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        # No timeout at first.
        self.assertIsNone(experiment.changes.latest_timeout())

        # Next, simulate a timeout.
        experiment.apply_lifecycle_state(lifecycle_timeout.value[-1])
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        # Timeout should be the latest changelog entry.
        self.assertEqual(
            experiment.changes.latest_timeout(), experiment.changes.latest_change()
        )

    def test_has_state_true(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_WAITING,
        )
        self.assertTrue(
            experiment.has_filter(
                Q(
                    status=NimbusExperiment.Status.DRAFT,
                    publish_status=NimbusExperiment.PublishStatus.WAITING,
                )
            )
        )

    def test_has_state_false(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_WAITING,
        )
        self.assertFalse(
            experiment.has_filter(
                Q(
                    status=NimbusExperiment.Status.DRAFT,
                    publish_status=NimbusExperiment.PublishStatus.IDLE,
                )
            )
        )

    @parameterized.expand(
        [
            [False, False, False, False, False],
            [True, False, False, True, False],
            [False, True, False, True, True],
            [False, False, True, True, True],
        ]
    )
    def test_signoff_recommendations(
        self,
        risk_brand,
        risk_revenue,
        risk_partner_related,
        vp_recommended,
        legal_recommended,
    ):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            risk_brand=risk_brand,
            risk_revenue=risk_revenue,
            risk_partner_related=risk_partner_related,
        )
        self.assertEqual(experiment.signoff_recommendations["qa_signoff"], True)
        self.assertEqual(experiment.signoff_recommendations["vp_signoff"], vp_recommended)
        self.assertEqual(
            experiment.signoff_recommendations["legal_signoff"], legal_recommended
        )


class TestNimbusBranch(TestCase):
    def test_str(self):
        branch = NimbusBranchFactory.create()
        self.assertEqual(str(branch), branch.name)


class TestNimbusDocumentLink(TestCase):
    def test_str(self):
        doco_link = NimbusDocumentationLinkFactory.create()
        self.assertEqual(str(doco_link), f"{doco_link.title} ({doco_link.link})")


@parameterized_class(("application",), [list(NimbusExperiment.Application)])
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
            experiment.application_config.randomization_unit,
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
            experiment.application_config.randomization_unit,
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
            experiment.application_config.randomization_unit,
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
            experiment.application_config.randomization_unit,
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


class TestNimbusChangeLogManager(TestCase):
    def test_latest_review_request_returns_none_for_no_review_request(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.changes.latest_review_request())

    def test_latest_review_request_returns_change_for_idle_to_review(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        change = generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertEqual(experiment.changes.latest_review_request(), change)

    def test_latest_review_request_returns_most_recent_review_request(self):
        reviewer = UserFactory()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.save()
        generate_nimbus_changelog(experiment, reviewer, "test message")

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        second_request = generate_nimbus_changelog(
            experiment, experiment.owner, "test message"
        )

        self.assertEqual(experiment.changes.latest_review_request(), second_request)

    def test_latest_rejection_returns_none_for_no_rejection(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.changes.latest_rejection())

    def test_latest_rejection_returns_rejection_for_review_to_idle(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )

        changes = []
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.IDLE,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            changes.append(
                generate_nimbus_changelog(experiment, experiment.owner, "test message")
            )

        self.assertEqual(experiment.changes.latest_review_request(), changes[0])
        self.assertEqual(experiment.changes.latest_rejection(), changes[1])

    def test_latest_rejection_returns_rejection_for_waiting_to_idle(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )

        changes = []
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
            NimbusExperiment.PublishStatus.IDLE,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            changes.append(
                generate_nimbus_changelog(experiment, experiment.owner, "test message")
            )

        self.assertEqual(experiment.changes.latest_review_request(), changes[0])
        self.assertEqual(experiment.changes.latest_rejection(), changes[3])

    def test_launch_to_live_is_not_considered_latest_rejection(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
        )

        experiment.status = NimbusExperiment.Status.LIVE
        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertIsNone(experiment.changes.latest_rejection())

    def test_stale_timeout_not_returned(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertIsNone(experiment.changes.latest_timeout())

    def test_stale_rejection_not_returned(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
        )
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
            NimbusExperiment.PublishStatus.IDLE,
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertIsNone(experiment.changes.latest_rejection())


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
            new_status=NimbusExperiment.Status.PREVIEW,
            message=None,
        )
        self.assertEqual(str(changelog), f"Draft > Preview by {user.email} on {now}")
