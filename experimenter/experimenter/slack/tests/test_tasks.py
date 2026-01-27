from unittest import mock

from django.test import TestCase

from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.slack import tasks


class TestNimbusSendSlackNotification(TestCase):
    @mock.patch("experimenter.slack.tasks.send_slack_notification")
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

    @mock.patch("experimenter.slack.tasks.send_slack_notification")
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

    @mock.patch("experimenter.slack.tasks.send_slack_notification")
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


class TestCheckExperimentAlerts(TestCase):
    def test_queries_live_and_complete_experiments(self):
        live_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )
        complete_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW
        )

        with mock.patch(
            "experimenter.slack.tasks.check_single_experiment_alerts.delay"
        ) as mock_check:
            tasks.check_experiment_alerts()
            self.assertEqual(mock_check.call_count, 2)
            called_ids = {call.args[0] for call in mock_check.call_args_list}
            self.assertEqual(called_ids, {live_exp.id, complete_exp.id})

    def test_handles_no_experiments(self):
        with mock.patch(
            "experimenter.slack.tasks.check_single_experiment_alerts.delay"
        ) as mock_check:
            tasks.check_experiment_alerts()
            self.assertEqual(mock_check.call_count, 0)

    def test_handles_exception_gracefully(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )

        with mock.patch(
            "experimenter.slack.tasks.check_single_experiment_alerts.delay",
            side_effect=Exception("Task spawn failed"),
        ):
            with self.assertRaises(Exception) as context:
                tasks.check_experiment_alerts()

            self.assertIn("Task spawn failed", str(context.exception))


class TestCheckSingleExperimentAlerts(TestCase):
    def test_spawns_child_alert_tasks(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )

        with (
            mock.patch(
                "experimenter.slack.tasks.check_analysis_errors.delay"
            ) as mock_errors,
            mock.patch(
                "experimenter.slack.tasks.check_analysis_ready.delay"
            ) as mock_ready,
        ):
            tasks.check_single_experiment_alerts(experiment.id)

            mock_errors.assert_called_once_with(experiment.id)
            mock_ready.assert_called_once_with(experiment.id)

    def test_handles_missing_experiment(self):
        with mock.patch("experimenter.slack.tasks.logger") as mock_logger:
            tasks.check_single_experiment_alerts(99999)
            mock_logger.error.assert_called_once_with("Experiment 99999 not found")

    def test_handles_exception_in_child_task(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )

        with (
            mock.patch(
                "experimenter.slack.tasks.check_analysis_errors.delay",
                side_effect=Exception("Child task failed"),
            ),
            self.assertRaises(Exception),
        ):
            tasks.check_single_experiment_alerts(experiment.id)
