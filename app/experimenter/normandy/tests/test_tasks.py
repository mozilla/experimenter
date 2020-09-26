import decimal
from datetime import date

import mock
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings

from experimenter.bugzilla.tests.mixins import MockBugzillaMixin
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.models import Experiment, ExperimentEmail
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.normandy import client as normandy
from experimenter.normandy import tasks
from experimenter.normandy.tests.mixins import MockNormandyMixin, MockNormandyTasksMixin


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestUpdateExperimentTask(MockNormandyTasksMixin, MockNormandyMixin, TestCase):
    def test_update_ready_to_ship_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_SHIP
        )
        mock_response_data = {
            "results": [
                {"id": 1, "latest_revision": {"creator": {"email": "dev@example.com"}}},
                {"id": 10},
                {"id": 100},
            ]
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200

        self.mock_normandy_requests_get.return_value = mock_response
        tasks.update_recipe_ids_to_experiments()

        experiment = Experiment.objects.get(id=experiment.id)

        self.assertEqual(experiment.status, Experiment.STATUS_ACCEPTED)
        self.assertEqual(experiment.normandy_id, 1)
        self.assertCountEqual(experiment.other_normandy_ids, [10, 100])

        self.assertTrue(
            experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_SHIP,
                new_status=Experiment.STATUS_ACCEPTED,
            ).exists()
        )

    def test_update_ready_to_ship_experiment_with_pre_existing_recipe(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=2
        )
        mock_response_data = {"results": [{"id": 2}, {"id": 10}, {"id": 100}]}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200

        self.mock_normandy_requests_get.return_value = mock_response
        tasks.update_recipe_ids_to_experiments()

        experiment = Experiment.objects.get(id=experiment.id)

        self.assertEqual(experiment.status, Experiment.STATUS_ACCEPTED)
        self.assertEqual(experiment.normandy_id, 2)
        self.assertCountEqual(experiment.other_normandy_ids, [10, 100])

        self.assertTrue(
            experiment.changes.filter(
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_ACCEPTED,
            ).exists()
        )

    def test_update_accepted_experiment_task(self):
        experiment = ExperimentFactory.create(
            status=Experiment.STATUS_ACCEPTED,
            normandy_id=1234,
            proposed_enrollment=60,
            proposed_duration=60,
        )

        tasks.update_launched_experiments()

        recipe = self.buildMockSuccessEnabledResponse().json()["approved_revision"]

        self.mock_tasks_add_start_date_comment.delay.assert_called_with(experiment.id)
        self.mock_tasks_set_is_paused_value.delay.assert_called_with(
            experiment.id, recipe
        )

        self.mock_tasks_comp_experiment_update_res.delay.assert_not_called()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].recipients(),
            [experiment.owner.email, experiment.analysis_owner],
        )

    def test_update_live_experiment_task(self):

        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=1234
        )

        self.mock_normandy_requests_get.return_value = (
            self.buildMockSuccessDisabledResponse()
        )
        tasks.update_launched_experiments()

        self.mock_tasks_comp_experiment_update_res.delay.assert_called_with(experiment.id)

        self.mock_tasks_set_is_paused_value.delay.assert_not_called()
        self.mock_tasks_add_start_date_comment.delay.assert_not_called()

        # No email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_ship_experiment_not_updated(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_SHIP
        )
        mock_response_data = {}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 404

        self.mock_normandy_requests_get.return_value = mock_response

        tasks.update_recipe_ids_to_experiments()

        self.assertEqual(experiment.status, Experiment.STATUS_SHIP)
        self.assertIsNone(experiment.normandy_id)
        self.assertIsNone(experiment.other_normandy_ids)

        self.assertFalse(
            experiment.changes.filter(
                old_status=Experiment.STATUS_SHIP,
                new_status=Experiment.STATUS_ACCEPTED,
            ).exists()
        )

    def test_update_live_experiment_not_updated(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=1234
        )

        tasks.update_launched_experiments()

        self.mock_tasks_add_start_date_comment.delay.assert_not_called()
        self.mock_tasks_comp_experiment_update_res.delay.assert_not_called()
        self.mock_tasks_set_is_paused_value.delay.assert_called()

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
        tasks.update_launched_experiments()

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

        mock_response_data = {
            "approved_revision": {"enabled": True, "enabled_states": [{"creator": None}]}
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200

        self.mock_normandy_requests_get.return_value = mock_response

        tasks.update_launched_experiments()
        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertTrue(
            experiment.changes.filter(
                changed_by__email="unknown-user@normandy.mozilla.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_one_failure_does_not_affect_other_experiment_status_updates(self):
        self.setUpMockNormandyFailWithSpecifiedID("1234")
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )

        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1235
        )

        tasks.update_launched_experiments()
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

    def test_experiment_without_normandy_ids(self):
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=None
        )
        tasks.update_launched_experiments()
        self.mock_normandy_requests_get.assert_not_called()

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

        tasks.update_launched_experiments()

        self.assertEqual(len(mail.outbox), 1)

    def test_accepted_experiment_becomes_live_if_normandy_enabled(self):

        experiment = ExperimentFactory.create(
            normandy_id=1234,
            proposed_start_date=date.today(),
            proposed_duration=30,
            proposed_enrollment=1,
        )

        experiment.status = Experiment.STATUS_LIVE
        experiment.save()

        tasks.update_launched_experiments()
        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].recipients(),
            [experiment.owner.email, experiment.analysis_owner],
        )

    def test_live_rollout_updates_population_percent(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            population_percent=decimal.Decimal("25.000"),
        )

        mock_response_data = {
            "approved_revision": {
                "enabled": True,
                "filter_object": [
                    {"type": "bucketSample", "count": 5000, "total": 10000}
                ],
            }
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200

        self.mock_normandy_requests_get.return_value = mock_response

        tasks.update_launched_experiments()
        experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(experiment.population_percent, decimal.Decimal("50.000"))

    def test_firefox_version_updates(self):
        experiment = ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            normandy_id=1234,
            firefox_min_version="80.0",
            firefox_max_version="80.0",
        )

        mock_response_data = {
            "approved_revision": {
                "enabled": True,
                "filter_object": [
                    {"type": "version", "versions": [79.0, 80.0, 81.0, 82.0]}
                ],
            }
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200

        self.mock_normandy_requests_get.return_value = mock_response

        tasks.update_launched_experiments()
        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.firefox_min_version, "79.0")
        self.assertEqual(experiment.firefox_max_version, "82.0")

        self.assertTrue(experiment.changes.filter(message="Added Version(s)").exists())

    def test_live_isHighPopulation_update(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            status=Experiment.STATUS_LIVE,
            normandy_id=1234,
        )

        mock_response_data = {
            "approved_revision": {
                "enabled": True,
                "arguments": {"isHighPopulation": True},
            }
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200

        self.assertFalse(experiment.is_high_population)

        self.mock_normandy_requests_get.return_value = mock_response

        tasks.update_launched_experiments()
        experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(experiment.is_high_population, True)


class TestUpdateExperimentSubTask(MockNormandyMixin, MockBugzillaMixin, TestCase):
    def test_update_status_task(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED
        )
        recipe_data = normandy.get_recipe(experiment.normandy_id)
        tasks.update_status_task(experiment, recipe_data)
        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)

        self.assertTrue(
            experiment.changes.filter(
                changed_by__email="dev@example.com",
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_set_is_paused_value_task(self):

        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=12345
        )
        recipe_data = normandy.get_recipe(experiment.normandy_id)

        tasks.set_is_paused_value_task(experiment.id, recipe_data)

        experiment = Experiment.objects.get(id=experiment.id)

        self.assertTrue(experiment.is_paused)
        self.assertTrue(
            experiment.changes.filter(
                changed_by__email=settings.NORMANDY_DEFAULT_CHANGELOG_USER,
                message="Enrollment Completed",
            )
        )

    def test_experiment_with_re_enabled_enrollment(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=1234, is_paused=True
        )
        self.mock_normandy_requests_get.return_value = (
            self.buildMockSucessWithNoPauseEnrollment()
        )
        recipe_data = normandy.get_recipe(experiment.normandy_id)
        tasks.set_is_paused_value_task(experiment.id, recipe_data)
        experiment = Experiment.objects.get(normandy_id=1234)

        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertFalse(experiment.is_paused)

        self.assertEquals(experiment.changes.latest().message, "Enrollment Re-enabled")

    def test_set_is_paused_value_with_bad_recipe(self):

        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=12345
        )
        recipe_data = {}

        tasks.set_is_paused_value_task(experiment.id, recipe_data)

        experiment = Experiment.objects.get(id=experiment.id)

        self.assertFalse(experiment.is_paused)
        self.assertFalse(
            experiment.changes.filter(
                changed_by__email=settings.NORMANDY_DEFAULT_CHANGELOG_USER,
                message="Enrollment Completed",
            ).exists()
        )
