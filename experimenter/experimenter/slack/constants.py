"""Slack constants and message templates."""

from experimenter.experiments.constants import NimbusConstants


class SlackConstants:
    """Slack constants, message templates, and action mappings."""

    # Slack action constants
    SLACK_ACTION_LAUNCH_REQUEST = "launch_request"
    SLACK_ACTION_UPDATE_REQUEST = "update_request"
    SLACK_ACTION_END_ENROLLMENT_REQUEST = "end_enrollment_request"
    SLACK_ACTION_END_EXPERIMENT_REQUEST = "end_experiment_request"

    # Slack operation names for logging
    SLACK_OPERATION_LAUNCH_SUCCESS = "launch success notification"
    SLACK_OPERATION_UPDATE_SUCCESS = "update success notification"
    SLACK_OPERATION_ENROLLMENT_ENDING = "enrollment ending notification"
    SLACK_OPERATION_EXPERIMENT_ENDING = "experiment ending notification"

    # Slack form action text mappings
    SLACK_FORM_ACTIONS = {
        SLACK_ACTION_LAUNCH_REQUEST: "🚀 Requests launch",
        SLACK_ACTION_UPDATE_REQUEST: "🔄 Requests update",
        SLACK_ACTION_END_ENROLLMENT_REQUEST: "⏸️ Requests end enrollment",
        SLACK_ACTION_END_EXPERIMENT_REQUEST: "🛑 Requests end experiment",
    }

    # Slack email action text mappings
    SLACK_EMAIL_ACTIONS = {
        NimbusConstants.EmailType.EXPERIMENT_END: "🛑 Is ready to end",
        NimbusConstants.EmailType.ENROLLMENT_END: "⏸️ Is ready to end enrollment",
    }

    # Slack action to alert type mappings
    SLACK_ACTION_TO_ALERT_TYPE = {
        SLACK_ACTION_LAUNCH_REQUEST: NimbusConstants.AlertType.LAUNCH_REQUEST,
        SLACK_ACTION_UPDATE_REQUEST: NimbusConstants.AlertType.UPDATE_REQUEST,
        SLACK_ACTION_END_ENROLLMENT_REQUEST: (
            NimbusConstants.AlertType.END_ENROLLMENT_REQUEST
        ),
        SLACK_ACTION_END_EXPERIMENT_REQUEST: (
            NimbusConstants.AlertType.END_EXPERIMENT_REQUEST
        ),
    }

    # Slack emoji reaction names
    class EmojiReaction:
        PENDING = "question"
        CANCEL = "x"
        APPROVE = "eyes"

    # Slack API error codes
    class ErrorCode:
        ALREADY_REACTED = "already_reacted"

    # Slack message templates
    SLACK_DM_PREFIX = "🔔 Join {channel} to get slack notifications: {message}"
    SLACK_DM_CHANNEL_LINK_SUFFIX = "\n\n🔗 View in channel: {channel_message_link}"
    SLACK_LAUNCH_SUCCESS_MESSAGE = (
        "🎉 ✅ *{name}* is now LIVE!\n📊 View experiment: <{url}|{slug}>"
    )
    SLACK_UPDATE_SUCCESS_MESSAGE = (
        "🔄 ✅ *{name}* update has been published\n📊 View experiment: <{url}|{slug}>"
    )
    SLACK_ENROLLMENT_ENDED_MESSAGE = (
        "⏹️ ✅ Enrollment for *{name}* has ended\n📊 View experiment: <{url}|{slug}>"
    )
    SLACK_EXPERIMENT_ENDED_MESSAGE = (
        "🛑 ✅ *{name}* has ended\n📊 View experiment: <{url}|{slug}>"
    )
    SLACK_RESULTS_READY_MESSAGE = "📈 {window} analysis results are now available"
    SLACK_ANALYSIS_ERRORS_MESSAGE = "⚠️ Analysis errors detected:\n{error_lines}"

    # Slack notification log messages
    SLACK_LOG_NOT_CONFIGURED = "Slack not configured, skipping {operation}"
    SLACK_LOG_NOTIFICATION_SENT = "Slack notification sent for experiment {experiment}"
    SLACK_LOG_LAUNCH_SUCCESS_SENT = "Sent launch success message for {experiment}"
    SLACK_LOG_UPDATE_SUCCESS_SENT = "Sent update success message for {experiment}"
    SLACK_LOG_ENROLLMENT_ENDING_SENT = (
        "Sent enrollment ending notification for {experiment}"
    )
    SLACK_LOG_EXPERIMENT_ENDING_SENT = (
        "Sent experiment ending notification for {experiment}"
    )
    SLACK_LOG_EYES_EMOJI_ADDED = "Added eyes emoji to launch message for {experiment}"
    SLACK_LOG_DM_SENT = "DM sent to user {user_id}"
    SLACK_LOG_USER_IN_CHANNEL = (
        "Skipping DM to user {user_id} - already in channel {channel}"
    )
    SLACK_LOG_EXPERIMENT_NOT_FOUND = "Experiment {experiment_id} not found"
    SLACK_LOG_NO_SLACK_THREAD = "No Slack thread found for {experiment}"
    SLACK_LOG_NO_CHANNEL_ID = "No channel ID found for alert {alert_id}"
    SLACK_LOG_COULD_NOT_FIND_USER = "Could not find Slack user for {email}"
    SLACK_LOG_FAILED_CHECK_USER_IN_CHANNEL = (
        "Failed to check if user {user_id} is in channel {channel}"
    )
    SLACK_LOG_COULD_NOT_GET_PERMALINK = "Could not get permalink for channel message"
    SLACK_LOG_FAILED_SEND_NOTIFICATION = (
        "Failed to send Slack notification for {experiment}"
    )
    SLACK_LOG_FAILED_SEND_DM = "Failed to send DM to user {user_id}"
    SLACK_LOG_FAILED_SEND_LAUNCH_SUCCESS = (
        "Failed to send launch success message for {experiment}"
    )
    SLACK_LOG_FAILED_ADD_EYES_EMOJI = (
        "Failed to add eyes emoji to launch message for {experiment}"
    )
    SLACK_LOG_EMOJI_ADDED = "Added {emoji_name} emoji to message for {experiment}"
    SLACK_LOG_FAILED_ADD_EMOJI = (
        "Failed to add {emoji_name} emoji to message for {experiment}"
    )
    SLACK_LOG_EMOJI_REMOVED = "Removed {emoji_name} emoji from message for {experiment}"
    SLACK_LOG_FAILED_REMOVE_EMOJI = (
        "Failed to remove {emoji_name} emoji from message for {experiment}"
    )

    # Slack task log messages
    SLACK_LOG_CHECKING_ALERTS = "Checking {count} experiments for alerts"
    SLACK_LOG_ALERTS_SPAWNED = "Spawned {count} alert check tasks"
    SLACK_LOG_CHECKING_EXPERIMENT = "Checking alerts for experiment: {experiment}"
    SLACK_LOG_ERROR_CHECKING_ALERTS = "Error in check_experiment_alerts"
    SLACK_LOG_ERROR_CHECKING_EXPERIMENT = (
        "Error checking alerts for experiment {experiment_id}"
    )
    SLACK_LOG_RESULTS_READY_SENT = (
        "Sent {window} results ready alert for experiment {experiment}"
    )
    SLACK_LOG_ANALYSIS_ERROR_SENT = "Sent analysis error alert for {experiment}"
    SLACK_LOG_FAILED_SEND_RESULTS_ALERT = (
        "Failed to send {window} results alert for experiment {experiment}"
    )
    SLACK_LOG_FAILED_SEND_ERROR_ALERT = "Failed to send error alert for {experiment}"
    SLACK_LOG_NOTIFICATION_TASK_SENT = (
        "Slack notification sent for experiment {experiment_id}"
    )
    SLACK_LOG_NOTIFICATION_TASK_FAILED = (
        "Sending Slack notification for experiment {experiment_id} failed"
    )
    SLACK_LOG_ERROR_ADDING_EMOJI = (
        "Error adding {emoji_name} emoji to message for experiment {experiment_id}"
    )
