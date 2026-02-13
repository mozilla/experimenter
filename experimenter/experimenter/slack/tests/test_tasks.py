from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusAlert
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.slack import tasks

AnalysisWindow = NimbusConstants.AnalysisWindow


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
    def test_queries_live_and_recent_complete_experiments(self):
        live_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )
        # Recent COMPLETE experiment (ended 1 day ago)
        recent_complete_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            _computed_end_date=(timezone.now() - timedelta(days=1)).date(),
        )
        # Old COMPLETE experiment (ended 5 days ago) - should be excluded
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            _computed_end_date=(timezone.now() - timedelta(days=5)).date(),
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
            self.assertEqual(called_ids, {live_exp.id, recent_complete_exp.id})

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
    def test_checks_experiment_alerts(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )

        with mock.patch("experimenter.slack.tasks.logger") as mock_logger:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_logger.debug.assert_called_once_with(
                f"Checking alerts for experiment: {experiment.slug}"
            )
            mock_logger.error.assert_not_called()
            mock_logger.exception.assert_not_called()

    def test_handles_missing_experiment(self):
        with mock.patch("experimenter.slack.tasks.logger") as mock_logger:
            tasks.check_single_experiment_alerts(99999)
            mock_logger.error.assert_called_once_with("Experiment 99999 not found")
            mock_logger.debug.assert_not_called()

    def test_handles_exception_during_processing(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )

        with (
            mock.patch(
                "experimenter.slack.tasks.NimbusExperiment.objects.get",
                side_effect=Exception("Database error"),
            ),
            mock.patch("experimenter.slack.tasks.logger") as mock_logger,
        ):
            with self.assertRaises(Exception) as context:
                tasks.check_single_experiment_alerts(experiment.id)

            self.assertIn("Database error", str(context.exception))
            mock_logger.exception.assert_called_once()
            call_args = mock_logger.exception.call_args[0][0]
            self.assertIn(str(experiment.id), call_args)


class TestCheckResultsReady(TestCase):
    def test_sends_alert_for_weekly_results(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "weekly": {
                        "enrollments": {"all": [{"point": 1, "upper": 2, "lower": 0}]}
                    }
                }
            },
        )

        expected_message = (
            f"{AnalysisWindow.WEEKLY.label} analysis results are now available"
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_send_slack.assert_called_once()
            call_args = mock_send_slack.call_args
            self.assertEqual(call_args[1]["experiment_id"], experiment.id)
            self.assertEqual(call_args[1]["action_text"], expected_message)
            self.assertEqual(call_args[1]["email_addresses"], [experiment.owner.email])

        alert = NimbusAlert.objects.get(
            experiment=experiment,
            alert_type=NimbusConstants.AlertType.ANALYSIS_READY_WEEKLY,
        )
        self.assertEqual(alert.message, expected_message)

    def test_sends_alert_for_overall_results(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "overall": {
                        "exposures": {"all": [{"point": 1, "upper": 2, "lower": 0}]}
                    }
                }
            },
        )

        expected_message = (
            f"{AnalysisWindow.OVERALL.label} analysis results are now available"
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_send_slack.assert_called_once()
            call_args = mock_send_slack.call_args
            self.assertEqual(call_args[1]["action_text"], expected_message)

        self.assertTrue(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_READY_OVERALL,
            ).exists()
        )

    def test_sends_alerts_for_both_weekly_and_overall(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "weekly": {
                        "enrollments": {"all": [{"point": 1, "upper": 2, "lower": 0}]}
                    },
                    "overall": {
                        "enrollments": {"all": [{"point": 1, "upper": 2, "lower": 0}]}
                    },
                }
            },
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            self.assertEqual(mock_send_slack.call_count, 2)

        self.assertEqual(NimbusAlert.objects.filter(experiment=experiment).count(), 2)
        self.assertTrue(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_READY_WEEKLY,
            ).exists()
        )
        self.assertTrue(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_READY_OVERALL,
            ).exists()
        )

    def test_does_not_send_duplicate_alerts(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "weekly": {
                        "enrollments": {"all": [{"point": 1, "upper": 2, "lower": 0}]}
                    }
                }
            },
        )

        message = f"{AnalysisWindow.WEEKLY.label} analysis results are now available"

        NimbusAlert.objects.create(
            experiment=experiment,
            alert_type=NimbusConstants.AlertType.ANALYSIS_READY_WEEKLY,
            message=message,
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_send_slack.assert_not_called()

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_READY_WEEKLY,
            ).count(),
            1,
        )

    def test_no_alert_when_no_results_data(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING, results_data=None
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_send_slack.assert_not_called()

        self.assertEqual(NimbusAlert.objects.filter(experiment=experiment).count(), 0)

    def test_no_alert_when_results_empty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={"v3": {"weekly": {}, "overall": {}}},
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_send_slack.assert_not_called()

        self.assertEqual(NimbusAlert.objects.filter(experiment=experiment).count(), 0)

    def test_no_alert_when_results_array_empty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={"v3": {"weekly": {"enrollments": {"all": []}}}},
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_send_slack.assert_not_called()

        self.assertEqual(NimbusAlert.objects.filter(experiment=experiment).count(), 0)

    def test_handles_slack_notification_failure(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "weekly": {
                        "enrollments": {"all": [{"point": 1, "upper": 2, "lower": 0}]}
                    }
                }
            },
        )

        with (
            mock.patch(
                "experimenter.slack.tasks.send_slack_notification",
                side_effect=Exception("Slack API error"),
            ),
            mock.patch("experimenter.slack.tasks.logger") as mock_logger,
            mock.patch("experimenter.slack.tasks.metrics") as mock_metrics,
        ):
            with self.assertRaises(Exception) as context:
                tasks.check_single_experiment_alerts(experiment.id)

            self.assertIn("Slack API error", str(context.exception))
            mock_logger.error.assert_called_once()
            mock_metrics.incr.assert_called_with("results_ready_alert.weekly.failed")

        self.assertEqual(NimbusAlert.objects.filter(experiment=experiment).count(), 0)


class TestCheckAnalysisErrors(TestCase):
    def test_sends_alert_for_analysis_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [
                            {
                                "exception_type": "UnexpectedException",
                                "message": "Unexpected error occurred",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ],
                        "default_browser_action": [
                            {
                                "exception_type": "StatisticComputationException",
                                "message": "Error computing statistic",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ],
                    }
                }
            },
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)

            mock_send_slack.assert_called_once()
            call_args = mock_send_slack.call_args
            self.assertEqual(call_args[1]["experiment_id"], experiment.id)
            self.assertIn("Analysis errors detected", call_args[1]["action_text"])
            self.assertIn(
                "experiment: UnexpectedException", call_args[1]["action_text"]
            )
            self.assertIn(
                "default_browser_action: StatisticComputationException",
                call_args[1]["action_text"],
            )
            self.assertEqual(call_args[1]["email_addresses"], [experiment.owner.email])

        alert = NimbusAlert.objects.get(
            experiment=experiment,
            alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
        )
        self.assertIn("Analysis errors detected", alert.message)

    def test_does_not_resend_same_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [
                            {
                                "exception_type": "UnexpectedException",
                                "message": "Unexpected error occurred",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ]
                    }
                }
            },
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            self.assertEqual(mock_send_slack.call_count, 1)

        # Second run with same errors - should not send alert
        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            mock_send_slack.assert_not_called()

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            1,
        )

    def test_sends_new_alert_for_different_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [
                            {
                                "exception_type": "UnexpectedException",
                                "message": "Unexpected error occurred",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ]
                    }
                }
            },
        )

        # First alert
        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            self.assertEqual(mock_send_slack.call_count, 1)

        # Update experiment with different error
        experiment.results_data = {
            "v3": {
                "errors": {
                    "experiment": [
                        {
                            "exception_type": "UnexpectedException",
                            "message": "Unexpected error occurred",
                            "analysis_basis": "enrollments",
                            "segment": "all",
                        }
                    ],
                    "default_browser_action": [
                        {
                            "exception_type": "StatisticComputationException",
                            "message": "Error computing statistic",
                            "analysis_basis": "enrollments",
                            "segment": "all",
                        }
                    ],
                }
            }
        }
        experiment.save()

        # Second run with additional error - should send new alert
        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            self.assertEqual(mock_send_slack.call_count, 1)

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            1,
        )

    def test_no_alert_when_no_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={"v3": {}},
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            mock_send_slack.assert_not_called()

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            0,
        )

    def test_no_alert_when_errors_empty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={"v3": {"errors": {}}},
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            mock_send_slack.assert_not_called()

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            0,
        )

    def test_no_alert_when_no_results_data(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING, results_data=None
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            mock_send_slack.assert_not_called()

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            0,
        )

    def test_no_alert_when_error_missing_exception_type(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [
                            {
                                "message": "No enrollment period",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ]
                    }
                }
            },
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            mock_send_slack.assert_not_called()

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            0,
        )

    def test_skips_empty_error_lists(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [],
                        "default_browser_action": [
                            {
                                "exception_type": "StatisticComputationException",
                                "message": "Error computing statistic",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ],
                    }
                }
            },
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            mock_send_slack.assert_called_once()
            call_args = mock_send_slack.call_args
            self.assertIn("Analysis errors detected", call_args[1]["action_text"])
            self.assertNotIn("experiment:", call_args[1]["action_text"])
            self.assertIn(
                "default_browser_action: StatisticComputationException",
                call_args[1]["action_text"],
            )

    def test_ignores_expected_error_types(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [
                            {
                                "exception_type": "NoEnrollmentPeriodException",
                                "message": "No enrollment period",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ],
                        "default_browser_action": [
                            {
                                "exception_type": "RolloutSkipException",
                                "message": "Rollout skipped",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ],
                    }
                }
            },
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            # Neither error should trigger an alert since both are ignorable
            mock_send_slack.assert_not_called()

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            0,
        )

    def test_alerts_on_non_ignorable_error_types(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [
                            {
                                "exception_type": "NoEnrollmentPeriodException",
                                "message": "No enrollment period",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ],
                        "default_browser_action": [
                            {
                                "exception_type": "UnexpectedException",
                                "message": "Unexpected error occurred",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ],
                    }
                }
            },
        )

        with mock.patch(
            "experimenter.slack.tasks.send_slack_notification"
        ) as mock_send_slack:
            tasks.check_single_experiment_alerts(experiment.id)
            # Only UnexpectedException should trigger an alert
            mock_send_slack.assert_called_once()
            call_args = mock_send_slack.call_args
            self.assertIn("Analysis errors detected", call_args[1]["action_text"])
            self.assertNotIn("NoEnrollmentPeriodException", call_args[1]["action_text"])
            self.assertIn("UnexpectedException", call_args[1]["action_text"])

    def test_handles_error_alert_slack_failure(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            results_data={
                "v3": {
                    "errors": {
                        "experiment": [
                            {
                                "exception_type": "StatisticComputationException",
                                "message": "Error computing statistic",
                                "analysis_basis": "enrollments",
                                "segment": "all",
                            }
                        ]
                    }
                }
            },
        )

        with (
            mock.patch(
                "experimenter.slack.tasks.send_slack_notification",
                side_effect=Exception("Slack API error"),
            ),
            mock.patch("experimenter.slack.tasks.logger") as mock_logger,
            mock.patch("experimenter.slack.tasks.metrics") as mock_metrics,
        ):
            with self.assertRaises(Exception) as context:
                tasks.check_single_experiment_alerts(experiment.id)

            self.assertIn("Slack API error", str(context.exception))
            mock_logger.error.assert_called_once()
            mock_metrics.incr.assert_called_with("analysis_error_alert.failed")

        self.assertEqual(
            NimbusAlert.objects.filter(
                experiment=experiment,
                alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            ).count(),
            0,
        )
