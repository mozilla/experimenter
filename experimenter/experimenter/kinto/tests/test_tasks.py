from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from kinto_http import KintoException
from parameterized import parameterized

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import (
    NimbusChangeLog,
    NimbusEmail,
    NimbusExperiment,
)
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.kinto import tasks
from experimenter.kinto.client import KINTO_REVIEW_STATUS, KINTO_ROLLBACK_STATUS
from experimenter.kinto.tests.mixins import MockKintoClientMixin

PREFFLIPS_PARAMETERIZED_CASES = [
    (
        "test-feature",
        settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
        settings.KINTO_COLLECTION_NIMBUS_SECURE,
    ),
    (
        "prefFlips",
        settings.KINTO_COLLECTION_NIMBUS_SECURE,
        settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
    ),
]


class TestNimbusCheckKintoPushQueue(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        mock_dispatchee_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_check_kinto_push_queue_by_collection.delay"
        )
        self.mock_dispatchee_task = mock_dispatchee_task_patcher.start()
        self.addCleanup(mock_dispatchee_task_patcher.stop)

    def test_dispatches_check_push_queue(self):
        tasks.nimbus_check_kinto_push_queue()
        for collection in (
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            settings.KINTO_COLLECTION_NIMBUS_MOBILE,
            settings.KINTO_COLLECTION_NIMBUS_WEB,
        ):
            self.mock_dispatchee_task.assert_any_call(collection)


@staticmethod
def create_desktop_feature(slug):
    return NimbusFeatureConfigFactory.create(
        name=slug,
        slug=slug,
        application=NimbusExperiment.Application.DESKTOP,
    )


class KintoTaskTestUtilsMixin:
    def _assert_experiment_status_unchanged(self, experiment):
        old_status = experiment.status
        old_publish_status = experiment.publish_status

        experiment.refresh_from_db()

        self.assertEqual(old_status, experiment.status)
        self.assertEqual(old_publish_status, experiment.publish_status)

    def _assert_experiment_status_changed(
        self,
        experiment,
        *,
        old_status,
        new_status,
        old_publish_status,
        new_publish_status,
        filter_kwargs=None,
    ):
        if filter_kwargs is None:
            filter_kwargs = {}

        self.assertEqual(experiment.status, old_status)
        self.assertEqual(experiment.publish_status, old_publish_status)

        experiment.refresh_from_db()
        self.assertEqual(experiment.status, new_status)
        self.assertEqual(experiment.publish_status, new_publish_status)
        self.assertTrue(
            experiment.changes.filter(
                old_status=old_status,
                new_status=new_status,
                old_publish_status=old_publish_status,
                new_publish_status=new_publish_status,
                **filter_kwargs,
            ).exists()
        )

    def _assert_check_collection_unchanged(self, collection):
        tasks.nimbus_check_kinto_push_queue_by_collection(collection)
        self.mock_push_task.assert_not_called()
        self.mock_update_task.assert_not_called()
        self.mock_end_task.assert_not_called()
        self.mock_kinto_client.patch_collection.assert_not_called()

    def _assert_check_collection_changed(
        self,
        collection,
        *,
        updated=None,
        ended=None,
        pushed=None,
        collection_patched=False,
    ):
        if not any((updated, ended, pushed, collection_patched)):
            raise ValueError("Expected at least one keyword arugment")

        tasks.nimbus_check_kinto_push_queue_by_collection(collection)

        if updated:
            self.mock_update_task.assert_called_once_with(collection, updated.id)
        else:
            self.mock_update_task.assert_not_called()

        if ended:
            self.mock_end_task.assert_called_once_with(collection, ended.id)
        else:
            self.mock_end_task.assert_not_called()

        if pushed:
            self.mock_push_task.assert_called_once_with(collection, pushed.id)
        else:
            self.mock_push_task.assert_not_called()

        if collection_patched:
            self.mock_kinto_client.patch_collection.assert_called_once_with(
                id=collection,
                data={"status": KINTO_ROLLBACK_STATUS},
                bucket=settings.KINTO_BUCKET_WORKSPACE,
            )
        else:
            self.mock_kinto_client.patch_collection.assert_not_called()

    def _assert_push_experiment_creates_record(self, collection, experiment):
        tasks.nimbus_push_experiment_to_kinto(collection, experiment.id)

        self.mock_kinto_client.create_record.assert_called_with(
            data=mock.ANY,
            collection=collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

    def _assert_update_experiment_updates_record(self, collection, experiment):
        tasks.nimbus_update_experiment_in_kinto(collection, experiment.id)

        self.mock_kinto_client.update_record.assert_called_with(
            data=NimbusExperimentSerializer(experiment).data,
            collection=collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_match='"0"',
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=collection,
            data={"status": KINTO_REVIEW_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def _assert_end_experiment_deletes_record(self, collection, experiment):
        tasks.nimbus_end_experiment_in_kinto(collection, experiment.id)

        self.mock_kinto_client.delete_record.assert_called_with(
            id=experiment.slug,
            collection=collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=collection,
            data={"status": KINTO_REVIEW_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )


class TestNimbusCheckKintoPushQueueByCollection(
    MockKintoClientMixin, KintoTaskTestUtilsMixin, TestCase
):
    def setUp(self):
        super().setUp()
        mock_push_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_push_experiment_to_kinto.delay"
        )
        self.mock_push_task = mock_push_task_patcher.start()
        self.addCleanup(mock_push_task_patcher.stop)

        mock_update_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_update_experiment_in_kinto.delay"
        )
        self.mock_update_task = mock_update_task_patcher.start()
        self.addCleanup(mock_update_task_patcher.stop)

        mock_end_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_end_experiment_in_kinto.delay"
        )
        self.mock_end_task = mock_end_task_patcher.start()
        self.addCleanup(mock_end_task_patcher.stop)

    def test_check_with_empty_queue_pushes_nothing(self):
        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_update_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_with_no_approved_publish_status_pushes_nothing(self):
        for lifecycle in [
            NimbusExperimentFactory.Lifecycles.CREATED,
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED,
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            NimbusExperimentFactory.Lifecycles.PAUSING_REVIEW_REQUESTED,
            NimbusExperimentFactory.Lifecycles.ENDING_REVIEW_REQUESTED,
        ]:
            NimbusExperimentFactory.create_with_lifecycle(
                lifecycle,
                application=NimbusExperiment.Application.DESKTOP,
            )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_update_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    @parameterized.expand(
        [
            (lifecycle, *params)
            for lifecycle in (
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
                NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            )
            for params in PREFFLIPS_PARAMETERIZED_CASES
        ]
    )
    @override_settings(KINTO_REVIEW_TIMEOUT=60)
    def test_check_with_pending_review_before_timeout_aborts_early(
        self, lifecycle, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=lifecycle,
            application=NimbusExperiment.Application.DESKTOP,
            with_latest_change_now=True,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(experiment)
        self.assertEqual(experiment.computed_end_date, experiment.proposed_end_date)

        self.setup_kinto_pending_review()

        self._assert_check_collection_unchanged(target_collection)
        self._assert_experiment_status_unchanged(experiment)
        self.assertEqual(experiment.computed_end_date, experiment.proposed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_approved_launch_and_no_kinto_pending_pushes_experiment(
        self,
        feature_slug,
        target_collection,
        alternate_collection,
    ):
        feature_config = create_desktop_feature(feature_slug)
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_approved_update_and_no_kinto_pending_updates_experiment(
        self,
        feature_slug,
        target_collection,
        alternate_collection,
    ):
        feature_config = create_desktop_feature(feature_slug)
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

        self._assert_check_collection_changed(
            target_collection, updated=launching_experiment
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_approved_end_and_no_kinto_pending_ends_experiment(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        ending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )
        self.assertEqual(
            ending_experiment.computed_end_date, ending_experiment.proposed_end_date
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(ending_experiment)

        self._assert_check_collection_changed(target_collection, ended=ending_experiment)
        self.assertEqual(
            ending_experiment.computed_end_date, ending_experiment.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    @override_settings(KINTO_REVIEW_TIMEOUT=0)
    def test_check_with_timeout_launch_review_and_queued_launch_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=timezone.now(),
            feature_configs=[feature_config],
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(pending_experiment)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertEqual(
            pending_experiment.computed_end_date, pending_experiment.proposed_end_date
        )
        self.assertIsNone(launching_experiment.computed_end_date)

        self.setup_kinto_pending_review()

        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )
        self._assert_experiment_status_changed(
            pending_experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.DRAFT,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        self.assertIsNone(pending_experiment.published_date)
        self.assertEqual(
            pending_experiment.computed_end_date, pending_experiment.proposed_end_date
        )
        self.assertIsNone(launching_experiment.computed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    @override_settings(KINTO_REVIEW_TIMEOUT=0)
    def test_check_with_timeout_update_review_and_queued_launch_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        expected_published_date = timezone.now()
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
            feature_configs=[feature_config],
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(pending_experiment)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertEqual(
            pending_experiment.computed_end_date, pending_experiment.proposed_end_date
        )
        self.assertIsNone(launching_experiment.computed_end_date)

        self.setup_kinto_pending_review()

        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )
        self._assert_experiment_status_changed(
            pending_experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        self.assertEqual(pending_experiment.published_date, expected_published_date)
        self.assertEqual(
            pending_experiment.computed_end_date, pending_experiment.proposed_end_date
        )
        self.assertIsNone(launching_experiment.computed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    @override_settings(KINTO_REVIEW_TIMEOUT=0)
    def test_check_with_timeout_end_review_and_queued_launch_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        expected_published_date = timezone.now()
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
            feature_configs=[feature_config],
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(pending_experiment)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertEqual(
            pending_experiment.computed_end_date, pending_experiment.proposed_end_date
        )
        self.assertIsNone(launching_experiment.computed_end_date)

        self.setup_kinto_pending_review()

        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )
        self._assert_experiment_status_changed(
            pending_experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        self.assertEqual(pending_experiment.published_date, expected_published_date)
        self.assertEqual(
            pending_experiment.computed_end_date, pending_experiment.proposed_end_date
        )
        self.assertIsNone(launching_experiment.computed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_rejected_launch_rolls_back_and_pushes(
        self,
        feature_slug,
        target_collection,
        alternate_collection,
    ):
        feature_config = create_desktop_feature(feature_slug)
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=timezone.now(),
            feature_configs=[feature_config],
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(rejected_experiment)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertIsNone(rejected_experiment.computed_end_date)
        self.assertIsNone(launching_experiment.computed_end_date)

        self.setup_kinto_rejected_review()
        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )
        self._assert_experiment_status_changed(
            rejected_experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.DRAFT,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )
        self.assertIsNone(rejected_experiment.status_next)
        self.assertIsNone(rejected_experiment.published_date)
        self.assertIsNone(rejected_experiment.computed_end_date)
        self.assertIsNone(launching_experiment.computed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_rejected_update_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        expected_published_date = timezone.now()
        feature_config = create_desktop_feature(feature_slug)
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
            feature_configs=[feature_config],
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(rejected_experiment)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertEqual(
            rejected_experiment.computed_end_date, rejected_experiment.proposed_end_date
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

        self.setup_kinto_rejected_review()

        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )
        self._assert_experiment_status_changed(
            rejected_experiment,
            old_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_status=NimbusExperiment.Status.LIVE,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )
        self.assertIsNone(rejected_experiment.status_next)
        self.assertFalse(rejected_experiment.is_paused)
        self.assertEqual(rejected_experiment.published_date, expected_published_date)
        self.assertEqual(
            rejected_experiment.computed_end_date, rejected_experiment.proposed_end_date
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_rejected_update_live_rollout_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        expected_published_date = timezone.now()
        feature_config = create_desktop_feature(feature_slug)
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            is_rollout_dirty=True,
            published_date=expected_published_date,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(rejected_experiment)
        self.assertEqual(
            rejected_experiment.computed_end_date, rejected_experiment.proposed_end_date
        )

        self.setup_kinto_rejected_review()

        self._assert_check_collection_changed(target_collection, collection_patched=True)
        self._assert_experiment_status_changed(
            rejected_experiment,
            old_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_status=NimbusExperiment.Status.LIVE,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )
        self.assertTrue(rejected_experiment.is_rollout_dirty)
        self.assertIsNone(rejected_experiment.status_next)
        self.assertFalse(rejected_experiment.is_paused)
        self.assertEqual(rejected_experiment.published_date, expected_published_date)
        self.assertEqual(
            rejected_experiment.computed_end_date, rejected_experiment.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_rejected_end_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        expected_published_date = timezone.now()
        feature_config = create_desktop_feature(feature_slug)
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
            feature_configs=[feature_config],
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(rejected_experiment)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertEqual(
            rejected_experiment.computed_end_date, rejected_experiment.proposed_end_date
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

        self.setup_kinto_rejected_review()
        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )

        self._assert_experiment_status_changed(
            rejected_experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )
        self.assertEqual(rejected_experiment.status_next, None)
        self.assertEqual(rejected_experiment.published_date, expected_published_date)
        self.assertEqual(
            rejected_experiment.computed_end_date, rejected_experiment.proposed_end_date
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_rollout_rejected_end_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        expected_published_date = timezone.now()
        feature_config = create_desktop_feature(feature_slug)
        rejected_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            published_date=expected_published_date,
            feature_configs=[feature_config],
        )
        launching_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(rejected_rollout)
        self._assert_experiment_status_unchanged(launching_rollout)
        self.assertEqual(
            rejected_rollout.computed_end_date, rejected_rollout.proposed_end_date
        )
        self.assertEqual(
            launching_rollout.computed_end_date, launching_rollout.proposed_end_date
        )

        self.setup_kinto_rejected_review()
        self._assert_check_collection_changed(
            target_collection, pushed=launching_rollout, collection_patched=True
        )
        self._assert_experiment_status_changed(
            rejected_rollout,
            old_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_status=NimbusExperiment.Status.LIVE,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )
        self.assertEqual(rejected_rollout.status_next, None)
        self.assertEqual(rejected_rollout.published_date, expected_published_date)
        self.assertEqual(
            rejected_rollout.computed_end_date, rejected_rollout.proposed_end_date
        )
        self.assertEqual(
            launching_rollout.computed_end_date, launching_rollout.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_dirty_rollout_rejected_end_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        expected_published_date = timezone.now()
        feature_config = create_desktop_feature(feature_slug)
        rejected_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            is_rollout_dirty=True,
            published_date=expected_published_date,
            feature_configs=[feature_config],
        )
        launching_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(rejected_rollout)
        self._assert_experiment_status_unchanged(launching_rollout)
        self.assertEqual(
            rejected_rollout.computed_end_date, rejected_rollout.proposed_end_date
        )
        self.assertEqual(
            launching_rollout.computed_end_date, launching_rollout.proposed_end_date
        )

        self.setup_kinto_rejected_review()

        self._assert_check_collection_changed(
            target_collection, pushed=launching_rollout, collection_patched=True
        )
        self._assert_experiment_status_changed(
            rejected_rollout,
            old_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_status=NimbusExperiment.Status.LIVE,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )
        self.assertEqual(rejected_rollout.status_next, None)
        self.assertTrue(rejected_rollout.is_rollout_dirty)
        self.assertEqual(rejected_rollout.published_date, expected_published_date)
        self.assertEqual(
            rejected_rollout.computed_end_date, rejected_rollout.proposed_end_date
        )
        self.assertEqual(
            launching_rollout.computed_end_date, launching_rollout.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_approved_update_sets_experiment_to_idle_saves_published_dto(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        updated_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            slug="updated_experiment",
            published_dto={
                "id": "updated_experiment",
                "something": "else",
                "last_modified": "123",
            },
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([updated_experiment.slug])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(updated_experiment)
        self.assertEqual(
            updated_experiment.computed_end_date, updated_experiment.proposed_end_date
        )

        self._assert_check_collection_unchanged(target_collection)
        self._assert_experiment_status_changed(
            updated_experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )

        self.assertIsNone(updated_experiment.status_next)
        self.assertEqual(
            updated_experiment.published_dto,
            {"id": updated_experiment.slug},
        )
        self.assertFalse(updated_experiment.is_rollout_dirty)
        self.assertEqual(
            updated_experiment.computed_end_date, updated_experiment.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_missing_review_and_queued_launch_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertIsNone(launching_experiment.computed_end_date)

        self.setup_kinto_pending_review()

        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )
        self.assertIsNone(launching_experiment.computed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_with_missing_rejection_and_queued_launch_rolls_back_and_pushes(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertIsNone(launching_experiment.computed_end_date)

        self.setup_kinto_rejected_review()
        self._assert_check_collection_changed(
            target_collection, pushed=launching_experiment, collection_patched=True
        )
        self.assertIsNone(launching_experiment.computed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_check_waiting_launching_experiment_with_signed_collection_becomes_rejection(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        waiting_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=timezone.now(),
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(waiting_experiment)
        self.assertIsNone(waiting_experiment.computed_end_date)

        self._assert_check_collection_unchanged(target_collection)
        self._assert_experiment_status_changed(
            waiting_experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.DRAFT,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
                "message": NimbusChangeLog.Messages.REJECTED_FROM_KINTO,
            },
        )
        self.assertIsNone(waiting_experiment.status_next)
        self.assertIsNone(waiting_experiment.published_date)
        self.assertIsNone(waiting_experiment.computed_end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_launching_experiment_live_when_record_is_in_main(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(launching_experiment)
        self.assertIsNone(launching_experiment.computed_end_date)
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

        self.setup_kinto_get_main_records([launching_experiment.slug])

        self._assert_check_collection_unchanged(target_collection)
        self._assert_experiment_status_changed(
            launching_experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
            },
        )
        self.assertIsNone(launching_experiment.status_next)
        self.assertEqual(
            launching_experiment.published_dto, {"id": launching_experiment.slug}
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )
        self.assertEqual(
            launching_experiment.computed_end_date, launching_experiment.proposed_end_date
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_ending_experiment_completed_when_record_is_not_in_main(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self.assertEqual(experiment1.computed_end_date, experiment1.proposed_end_date)
        self.assertEqual(experiment2.computed_end_date, experiment2.proposed_end_date)

        self.setup_kinto_get_main_records([experiment1.slug])

        self._assert_check_collection_unchanged(
            target_collection,
        )
        self._assert_experiment_status_unchanged(experiment1)
        self._assert_experiment_status_changed(
            experiment2,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            filter_kwargs={
                "changed_by__email": settings.KINTO_DEFAULT_CHANGELOG_USER,
                "message": NimbusChangeLog.Messages.COMPLETED,
            },
        )
        self.assertEqual(experiment1.computed_end_date, experiment1.proposed_end_date)
        self.assertEqual(experiment2.computed_end_date, experiment2.end_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_updating_experiment_with_published_dto_none_is_skipped(
        self, feature_slug, target_collection, alternate_collection
    ):
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_dto=None,
            feature_configs=[feature_config],
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        self._assert_check_collection_unchanged(alternate_collection)
        self._assert_experiment_status_unchanged(experiment)

        self.setup_kinto_get_main_records([experiment.slug])

        self._assert_check_collection_unchanged(target_collection)


class TestNimbusPushExperimentToKintoTask(
    MockKintoClientMixin, KintoTaskTestUtilsMixin, TestCase
):
    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_push_experiment_to_kinto(
        self,
        feature_slug,
        target_collection,
        *_unused,
    ):
        """Push desktop experiment to Kinto and validate its outgoing publish status,
        published_date, and changelogs"""
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=None,
            feature_configs=[feature_config],
        )

        self._assert_push_experiment_creates_record(target_collection, experiment)
        self._assert_experiment_status_changed(
            experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.DRAFT,
            old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
            new_publish_status=NimbusExperiment.PublishStatus.WAITING,
            filter_kwargs={
                "message": NimbusChangeLog.Messages.LAUNCHING_TO_KINTO,
            },
        )
        self.assertIsNotNone(experiment.published_date)

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_push_experiment_to_kinto_overwrites_existing_published_date_for_draft(
        self, feature_slug, target_collection, *_unused
    ):
        existing_published_date = timezone.now()
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=existing_published_date,
            feature_configs=[feature_config],
        )

        self._assert_push_experiment_creates_record(target_collection, experiment)
        self._assert_experiment_status_changed(
            experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.DRAFT,
            old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
            new_publish_status=NimbusExperiment.PublishStatus.WAITING,
            filter_kwargs={
                "message": NimbusChangeLog.Messages.LAUNCHING_TO_KINTO,
            },
        )
        self.assertIsNotNone(experiment.published_date)
        self.assertNotEqual(experiment.published_date, existing_published_date)

    def test_push_experiment_to_kinto_reraises_exception(self):
        feature_config = create_desktop_feature("test-feature")
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            feature_configs=[feature_config],
        )

        self.mock_kinto_client.create_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_push_experiment_to_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )


class TestNimbusUpdateExperimentInKinto(
    MockKintoClientMixin, KintoTaskTestUtilsMixin, TestCase
):
    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_updates_experiment_record_in_kinto(
        self, feature_slug, target_collection, *_unused
    ):
        existing_published_date = timezone.now()
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=existing_published_date,
            feature_configs=[feature_config],
        )

        self._assert_update_experiment_updates_record(target_collection, experiment)
        self._assert_experiment_status_changed(
            experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
            new_publish_status=NimbusExperiment.PublishStatus.WAITING,
            filter_kwargs={
                "message": NimbusChangeLog.Messages.UPDATING_IN_KINTO,
            },
        )
        self.assertEqual(experiment.published_date, existing_published_date)

    def test_update_experiment_in_kinto_reraises_exception(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.mock_kinto_client.update_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_update_experiment_in_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )


class TestNimbusEndExperimentInKinto(
    MockKintoClientMixin, KintoTaskTestUtilsMixin, TestCase
):
    def test_exception_for_failed_delete(self):
        feature_config = create_desktop_feature("test-feature")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )
        self.mock_kinto_client.delete_record.side_effect = Exception("test exception")
        with self.assertRaises(Exception):
            tasks.nimbus_end_experiment_in_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_end_experiment_in_kinto_deletes_experiment(
        self, feature_slug, target_collection, *_unused
    ):
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        self._assert_end_experiment_deletes_record(target_collection, experiment)
        self._assert_experiment_status_changed(
            experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
            new_publish_status=NimbusExperiment.PublishStatus.WAITING,
            filter_kwargs={
                "message": NimbusChangeLog.Messages.DELETING_FROM_KINTO,
            },
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_end_experiment_in_kinto_with_404_moves_to_waiting(
        self, feature_slug, target_collection, *_unused
    ):
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        exception = KintoException()
        exception.response = mock.Mock()
        exception.response.status_code = 404
        self.mock_kinto_client.delete_record.side_effect = exception

        tasks.nimbus_end_experiment_in_kinto(target_collection, experiment.id)

        self.mock_kinto_client.delete_record.assert_called_with(
            id=experiment.slug,
            collection=target_collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

        self._assert_experiment_status_changed(
            experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.LIVE,
            old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
            new_publish_status=NimbusExperiment.PublishStatus.WAITING,
            filter_kwargs={
                "message": NimbusChangeLog.Messages.DELETING_FROM_KINTO,
            },
        )

    @parameterized.expand(PREFFLIPS_PARAMETERIZED_CASES)
    def test_end_experiment_in_kinto_with_non_404_reraises(
        self, feature_slug, target_collection, *_unused
    ):
        feature_config = create_desktop_feature(feature_slug)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        exception = KintoException("test exception")
        exception.response = mock.Mock()
        exception.response.status_code = 400
        self.mock_kinto_client.delete_record.side_effect = exception

        with self.assertRaises(KintoException):
            tasks.nimbus_end_experiment_in_kinto(target_collection, experiment.id)


class TestNimbusSynchronizePreviewExperimentsInKinto(
    MockKintoClientMixin, KintoTaskTestUtilsMixin, TestCase
):
    @parameterized.expand(
        [
            NimbusExperiment.Application.FOCUS_IOS,
            NimbusExperiment.Application.FENIX,
            NimbusExperiment.Application.IOS,
            NimbusExperiment.Application.FOCUS_ANDROID,
            NimbusExperiment.Application.DESKTOP,
            NimbusExperiment.Application.MONITOR,
            NimbusExperiment.Application.FXA,
            NimbusExperiment.Application.DEMO_APP,
        ]
    )
    def test_publishes_preview_experiments_and_unpublishes_non_preview_experiments(
        self, application
    ):
        should_publish_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            published_date=None,
            application=application,
        )
        should_unpublish_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            published_date=timezone.now(),
            application=application,
        )

        self.setup_kinto_get_main_records([should_unpublish_experiment.slug])

        tasks.nimbus_synchronize_preview_experiments_in_kinto()

        data = NimbusExperimentSerializer(should_publish_experiment).data

        should_publish_experiment = NimbusExperiment.objects.get(
            id=should_publish_experiment.id
        )
        self.assertEqual(should_publish_experiment.published_dto, data)
        self.assertIsNotNone(should_publish_experiment.published_date)

        should_unpublish_experiment = NimbusExperiment.objects.get(
            id=should_unpublish_experiment.id
        )

        self.assertIsNone(should_unpublish_experiment.published_date)
        self.assertIsNone(should_unpublish_experiment.published_dto)

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=NimbusExperiment.APPLICATION_CONFIGS[
                application
            ].preview_collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )
        self.mock_kinto_client.delete_record.assert_called_with(
            id=should_unpublish_experiment.slug,
            collection=NimbusExperiment.APPLICATION_CONFIGS[
                application
            ].preview_collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def test_unpublishes_preview_experiments_older_than_30_days(self):
        old_preview_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            slug="old_preview_experiment",
            published_date=timezone.now(),
            application=NimbusExperiment.Application.DESKTOP,
        )

        recent_preview_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            slug="recent_preview_experiment",
            published_date=timezone.now(),
            application=NimbusExperiment.Application.DESKTOP,
        )

        thirty_one_days_ago = timezone.now() - timezone.timedelta(days=31)
        NimbusExperiment.objects.filter(id=old_preview_experiment.id).update(
            _updated_date_time=thirty_one_days_ago
        )

        self.setup_kinto_get_main_records(
            [old_preview_experiment.slug, recent_preview_experiment.slug]
        )

        tasks.nimbus_synchronize_preview_experiments_in_kinto()

        old_preview_experiment.refresh_from_db()
        self.assertIsNone(old_preview_experiment.published_date)
        self.assertEqual(old_preview_experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(
            old_preview_experiment.publish_status,
            NimbusExperiment.PublishStatus.IDLE,
        )

        expiration_changelog = old_preview_experiment.changes.filter(
            message=NimbusChangeLog.Messages.EXPIRED_FROM_PREVIEW,
            changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
        )
        self.assertTrue(expiration_changelog.exists())

        recent_preview_experiment.refresh_from_db()
        self.assertIsNotNone(recent_preview_experiment.published_date)
        self.assertEqual(
            recent_preview_experiment.status, NimbusExperiment.Status.PREVIEW
        )

        self.mock_kinto_client.delete_record.assert_called_with(
            id=old_preview_experiment.slug,
            collection=NimbusExperiment.APPLICATION_CONFIGS[
                NimbusExperiment.Application.DESKTOP
            ].preview_collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def test_reraises_exception(self):
        self.mock_kinto_client.create_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_synchronize_preview_experiments_in_kinto()


class TestNimbusSendEmails(MockKintoClientMixin, TestCase):
    def test_enrollment_ending_email_not_sent_for_experiments_before_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=20,
            with_latest_change_now=True,
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_enrollment_ending_email_not_sent_for_experiments_already_sent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=0,
            proposed_duration=20,
            with_latest_change_now=True,
        )

        NimbusEmail.objects.create(
            experiment=experiment, type=NimbusExperiment.EmailType.ENROLLMENT_END
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_enrollment_ending_email_sent_for_experiments_after_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=0,
            proposed_duration=20,
            with_latest_change_now=True,
            is_rollout=False,
        )

        tasks.nimbus_send_emails()

        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.ENROLLMENT_END
            ).exists()
        )
        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_enrollment_ending_email_not_sent_for_rollouts_after_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=0,
            proposed_duration=20,
            with_latest_change_now=True,
            is_rollout=True,
        )

        tasks.nimbus_send_emails()

        self.assertFalse(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.ENROLLMENT_END
            ).exists()
        )
        self.assertEqual(experiment.emails.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_experiment_ending_email_not_sent_for_experiments_before_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=20,
            with_latest_change_now=True,
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_experiment_ending_email_not_sent_for_experiments_already_sent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=0,
            with_latest_change_now=True,
        )

        NimbusEmail.objects.create(
            experiment=experiment, type=NimbusExperiment.EmailType.EXPERIMENT_END
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_experiment_ending_email_sent_for_experiments_after_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=0,
            with_latest_change_now=True,
        )

        tasks.nimbus_send_emails()

        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.EXPERIMENT_END
            ).exists()
        )
        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 1)


class TestNimbusSendSlackNotification(MockKintoClientMixin, TestCase):
    @mock.patch("experimenter.kinto.tasks.send_slack_notification")
    def test_sends_slack_notification_successfully(self, mock_send_slack):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        email_addresses = ["user1@example.com", "user2@example.com"]
        action_text = "requests launch"
        requesting_user_email = "requester@example.com"

        tasks.nimbus_send_slack_notification(
            experiment.id,
            email_addresses,
            action_text,
            requesting_user_email,
        )

        mock_send_slack.assert_called_once_with(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=action_text,
            requesting_user_email=requesting_user_email,
        )

    @mock.patch("experimenter.kinto.tasks.send_slack_notification")
    def test_sends_slack_notification_without_requesting_user(self, mock_send_slack):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        email_addresses = ["user1@example.com"]
        action_text = "ready to end"

        tasks.nimbus_send_slack_notification(
            experiment.id,
            email_addresses,
            action_text,
        )

        mock_send_slack.assert_called_once_with(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=action_text,
            requesting_user_email=None,
        )

    @mock.patch("experimenter.kinto.tasks.send_slack_notification")
    def test_slack_notification_reraises_exception(self, mock_send_slack):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        email_addresses = ["user1@example.com"]
        action_text = "requests launch"

        mock_send_slack.side_effect = Exception("Slack API error")

        with self.assertRaises(Exception) as context:
            tasks.nimbus_send_slack_notification(
                experiment.id,
                email_addresses,
                action_text,
            )

        self.assertIn("Slack API error", str(context.exception))
