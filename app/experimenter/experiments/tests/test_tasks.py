import markus
import mock

from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date

from markus.testing import MetricsMock
from requests.exceptions import RequestException
from django.core import mail
from experimenter.experiments import bugzilla, tasks
from experimenter.experiments.models import Experiment, ExperimentEmail
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    UserFactory,
)
from experimenter.experiments.tests.mixins import (
    MockBugzillaMixin,
    MockNormandyMixin,
    MockRequestMixin,
)
from experimenter.notifications.models import Notification


class TestCreateBugTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, bugzilla_id=None
        )

    def test_experiment_bug_successfully_created(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.create_experiment_bug_task(self.user.id, self.experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.create_experiment_bug.timing",
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.failed",
                )
            )

        self.mock_bugzilla_requests_post.assert_called()

        experiment = Experiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bugzilla_id, self.bugzilla_id)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_CREATE_BUG.format(
                bug_url=experiment.bugzilla_url
            ),
        )

    def test_bugzilla_error_creates_error_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_post.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.create_experiment_bug_task(
                    self.user.id, self.experiment.id
                )

                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.started",
                        value=1,
                    )
                )
                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.failed",
                        value=1,
                    )
                )
                # Failures should abort timing metrics.
                self.assertFalse(
                    mm.has_record(
                        markus.TIMING,
                        "experiments.tasks.create_experiment_bug.timing",
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.completed",
                    )
                )

        self.mock_bugzilla_requests_post.assert_called()
        self.assertEqual(Notification.objects.count(), 1)

        experiment = Experiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bugzilla_id, None)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message, tasks.NOTIFICATION_MESSAGE_CREATE_BUG_FAILED
        )


class TestUpdateTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        self.experiment.bugzilla_id = self.bugzilla_id
        self.experiment.save()

    def test_experiment_bug_successfully_updated(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.update_experiment_bug_task(self.user.id, self.experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.update_experiment_bug.timing",
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.failed",
                )
            )

        self.mock_bugzilla_requests_put.assert_called()

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_UPDATE_BUG.format(
                bug_url=self.experiment.bugzilla_url
            ),
        )

    def test_bugzilla_error_creates_notifications(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_put.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.update_experiment_bug_task(
                    self.user.id, self.experiment.id
                )

                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.update_experiment_bug.started",
                        value=1,
                    )
                )
                # Failures should abort timing metrics.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.update_experiment_bug.timing",
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.update_experiment_bug.completed",
                    )
                )

        self.mock_bugzilla_requests_put.assert_called()
        self.assertEqual(Notification.objects.count(), 1)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message, tasks.NOTIFICATION_MESSAGE_UPDATE_BUG_FAILED
        )

    def test_internal_only_does_not_update_bugzilla(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, risk_internal_only=True
        )

        with MetricsMock() as mm:
            tasks.update_experiment_bug_task(self.user.id, experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.started",
                    value=1,
                )
            )
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiements.tasks.update_experiment_bug.completed",
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.update_experiment_bug.timing",
                )
            )

            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "expeiments.tasks.update_experiement_bug.failed",
                )
            )

        self.mock_bugzilla_requests_put.assert_not_called()

        self.assertEqual(Notification.objects.count(), 0)


class TestUpdateExperimentStatus(
    MockRequestMixin, MockNormandyMixin, MockBugzillaMixin, TestCase
):

    def test_experiment_with_no_recipe_data(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )

        mock_response_data = {"approved_revision": None}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200

        self.mock_normandy_requests_get.return_value = mock_response
        tasks.update_experiment_info()

        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.status, Experiment.STATUS_ACCEPTED)
        self.assertFalse(
            experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_experiment_with_no_creator_in_recipe(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )

        recipe_data = {
            "approved_revision": {
                "enabled": True,
                "enabled_states": [{"creator": None}],
            }
        }

        tasks.update_status(experiment, recipe_data)
        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertTrue(
            experiment.changes.filter(
                changed_by__email="unknown-user@normandy.mozilla.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_experiment_with_pause_val_change(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=1234
        )
        self.assertFalse(experiment.is_paused)
        recipe_data = {"arguments": {"isEnrollmentPaused": True}}
        tasks.set_is_paused_value(experiment, recipe_data)
        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertTrue(experiment.is_paused)

        self.assertEquals(
            experiment.changes.latest().message, "Enrollment Completed"
        )

    def test_experiment_with_re_enabled_enrollment(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            is_paused=True,
        )
        recipe_data = {"arguments": {"isEnrollmentPaused": False}}
        tasks.set_is_paused_value(experiment, recipe_data)
        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertFalse(experiment.is_paused)

        self.assertEquals(
            experiment.changes.latest().message, "Enrollment Re-enabled"
        )

    def test_experiment_with_paused_staying_the_same(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            is_paused=False,
        )

        recipe_data = {"arguments": {"isEnrollmentPaused": False}}
        tasks.set_is_paused_value(experiment, recipe_data)

        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertFalse(experiment.is_paused)

    def test_accepted_experiment_becomes_live_if_normandy_enabled(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED,
            normandy_id=1234,
            proposed_start_date=date.today(),
            proposed_duration=30,
            proposed_enrollment=0,
        )

        tasks.update_experiment_info()
        experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertTrue(
            experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )
        # status is live so bugzilla should be called
        experiment = Experiment.objects.get(id=experiment.id)
        comment = "Start Date: {} End Date: {}".format(
            experiment.start_date, experiment.end_date
        )
        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
            {"comment": comment},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].recipients(), [experiment.owner.email])

    def test_experiment_without_normandy_ids(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=None
        )
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=None
        )
        tasks.update_experiment_info()
        self.mock_normandy_requests_get.assert_not_called()

    def test_accepted_experiment_stays_accepted_if_normandy_disabled(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )

        self.mock_normandy_requests_get.return_value = (
            self.buildMockSuccessDisabledResponse()
        )
        tasks.update_experiment_info()
        updated_experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(updated_experiment.status, Experiment.STATUS_ACCEPTED)
        self.assertFalse(
            updated_experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

        # status is still accepted so no bugzilla update
        self.mock_bugzilla_requests_post.assert_not_called()

    def test_live_experiment_stays_live_if_normandy_enabled(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=1234
        )
        tasks.update_experiment_info()
        updated_experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(updated_experiment.status, Experiment.STATUS_LIVE)
        self.assertFalse(
            updated_experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_LIVE,
                new_status=Experiment.STATUS_COMPLETE,
            ).exists()
        )

    def test_live_experiment_becomes_complete_if_normandy_disabled(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=1234
        )
        self.mock_normandy_requests_get.return_value = (
            self.buildMockSuccessDisabledResponse()
        )

        tasks.update_experiment_info()
        updated_experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(updated_experiment.status, Experiment.STATUS_COMPLETE)
        self.assertTrue(
            updated_experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_LIVE,
                new_status=Experiment.STATUS_COMPLETE,
            ).exists()
        )

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(
                id=updated_experiment.bugzilla_id
            ),
            {"status": "RESOLVED", "resolution": "FIXED"},
        )

    def test_one_failure_does_not_affect_other_experiment_status_updates(self):
        self.setUpMockNormandyFailWithSpecifiedID("1234")
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )

        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1235
        )

        tasks.update_experiment_info()
        updated_experiment = Experiment.objects.get(normandy_id=1234)
        updated_experiment2 = Experiment.objects.get(normandy_id=1235)
        self.assertEqual(updated_experiment.status, Experiment.STATUS_ACCEPTED)
        self.assertEqual(updated_experiment2.status, Experiment.STATUS_LIVE)
        self.assertFalse(
            updated_experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )
        self.assertTrue(
            updated_experiment2.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_experiment_status_updates_by_existing_user(self):
        User = get_user_model()
        user = UserFactory(email="dev@example.com")
        self.assertTrue(User.objects.filter(email="dev@example.com").exists())
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )
        tasks.update_experiment_info()
        experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertTrue(
            experiment.changes.filter(
                changed_by=user,
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_experiment_status_updates_by_new_user(self):
        User = get_user_model()

        self.assertFalse(User.objects.filter(email="dev@example.com").exists())
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )
        tasks.update_experiment_info()
        experiment = Experiment.objects.get(normandy_id=1234)
        user = User.objects.get(email="dev@example.com")
        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertTrue(
            experiment.changes.filter(
                changed_by=user,
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_send_experiment_ending_email(self):
        ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            proposed_start_date=date.today(),
            proposed_enrollment=0,
            proposed_duration=5,
        )
        ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            proposed_start_date=date.today(),
            proposed_duration=30,
            proposed_enrollment=0,
        )
        exp_3 = ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            proposed_start_date=date.today(),
            proposed_duration=4,
            proposed_enrollment=0,
        )

        ExperimentEmail.objects.create(
            experiment=exp_3, type=ExperimentConstants.EXPERIMENT_ENDS
        )

        tasks.update_experiment_info()

        self.assertEqual(len(mail.outbox), 1)

    def test_doesnt_send_experiment_status_emails_if_only_accepted(self):
        ExperimentFactory.create(
            status=Experiment.STATUS_ACCEPTED,
            proposed_start_date=date.today(),
            proposed_duration=5,
            proposed_enrollment=0,
        )
        ExperimentFactory.create(
            status=Experiment.STATUS_ACCEPTED,
            proposed_start_date=date.today(),
            proposed_duration=30,
            proposed_enrollment=5,
        )

        tasks.update_experiment_info()

        self.assertEqual(len(mail.outbox), 0)

    def test_send_enrollment_pausing_email(self):
        exp_1 = ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            proposed_start_date=date.today(),
            proposed_enrollment=4,
            proposed_duration=30,
        )
        ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            normandy_id=1111,
            proposed_start_date=date.today(),
            proposed_enrollment=5,
            proposed_duration=30,
        )
        ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            normandy_id=1111,
            proposed_start_date=date.today(),
            proposed_enrollment=8,
            proposed_duration=30,
        )

        ExperimentEmail.objects.create(
            experiment=exp_1, type=ExperimentConstants.EXPERIMENT_PAUSES
        )

        tasks.update_experiment_info()

        self.assertEqual(len(mail.outbox), 1)


class TestUpdateResolutionTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        self.experiment.bugzilla_id = self.bugzilla_id
        self.experiment.save()

    def test_experiment_bug_resolution_successfully_updated(self):
        self.assertEqual(Notification.objects.count(), 0)

        tasks.update_bug_resolution_task(self.user.id, self.experiment.id)

        self.mock_bugzilla_requests_put.assert_called()

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_ARCHIVE_COMMENT.format(
                bug_url=self.experiment.bugzilla_url
            ),
        )

    def test_no_request_call_when_no_bug_id(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, risk_internal_only=True
        )
        experiment.bugzilla_id = None
        experiment.save()

        tasks.update_bug_resolution_task(self.user.id, experiment.id)

        self.mock_bugzilla_requests_put.assert_not_called()

        self.assertEqual(Notification.objects.count(), 0)

    def test_bugzilla_error_create_notifications(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_put.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):

            tasks.update_bug_resolution_task(self.user.id, self.experiment.id)

            self.mock_bugzilla_requests_put.side_effect = RequestException()
            self.mock_bugzilla_requests_put.assert_called()
            self.assertEqual(Notification.objects.count(), 1)
            message = tasks.NOTIFICATION_MESSAGE_ARCHIVE_ERROR_MESSAGE.format(
                bug_url=self.experiment.bugzilla_url
            )
            self.assertEqual(
                Notification.objects.filters(message=message).exists()
            )
