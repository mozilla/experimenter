"""Slack constants and message templates."""

from experimenter.experiments.constants import NimbusConstants


class SlackConstants:
    """Slack constants, message templates, and action mappings."""

    # Slack action constants
    SLACK_ACTION_LAUNCH_REQUEST = "launch_request"
    SLACK_ACTION_UPDATE_REQUEST = "update_request"
    SLACK_ACTION_END_ENROLLMENT_REQUEST = "end_enrollment_request"
    SLACK_ACTION_END_EXPERIMENT_REQUEST = "end_experiment_request"
    SLACK_ACTION_ADVANCE_ROLLOUT_PHASE_REQUEST = "advance_rollout_phase_request"
    SLACK_ACTION_DISABLE_ROLLOUT_REQUEST = "disable_rollout_request"
    SLACK_ACTION_REENABLE_ROLLOUT_REQUEST = "reenable_rollout_request"

    # Slack operation names for logging
    SLACK_OPERATION_LAUNCH_SUCCESS = "launch success notification"
    SLACK_OPERATION_UPDATE_SUCCESS = "update success notification"
    SLACK_OPERATION_ENROLLMENT_ENDING = "enrollment ending notification"
    SLACK_OPERATION_EXPERIMENT_ENDING = "experiment ending notification"
    SLACK_OPERATION_ROLLOUT_PHASE_ADVANCE_SUCCESS = (
        "rollout phase advance success notification"
    )
    SLACK_OPERATION_ROLLOUT_DISABLE_SUCCESS = "rollout disable success notification"
    SLACK_OPERATION_ROLLOUT_REENABLE_SUCCESS = "rollout re-enable success notification"

    # Slack form action text mappings
    SLACK_FORM_ACTIONS = {
        SLACK_ACTION_LAUNCH_REQUEST: "🚀 Requests launch",
        SLACK_ACTION_UPDATE_REQUEST: "🔄 Requests update",
        SLACK_ACTION_END_ENROLLMENT_REQUEST: "⏸️ Requests end enrollment",
        SLACK_ACTION_END_EXPERIMENT_REQUEST: "🛑 Requests end experiment",
        SLACK_ACTION_ADVANCE_ROLLOUT_PHASE_REQUEST: "⏩ Requests rollout phase advance",
        SLACK_ACTION_DISABLE_ROLLOUT_REQUEST: "⏸️ Requests disable rollout",
        SLACK_ACTION_REENABLE_ROLLOUT_REQUEST: "▶️ Requests re-enable rollout",
    }

    # Slack email action text mappings
    SLACK_EMAIL_ACTIONS = {
        NimbusConstants.EmailType.EXPERIMENT_END: "🛑 Ready to end experiment",
        NimbusConstants.EmailType.ENROLLMENT_END: "⏸️ Ready to end enrollment",
        NimbusConstants.EmailType.ROLLOUT_PHASE_ADVANCE: (
            "⏩ Ready to advance rollout phase"
        ),
    }
    SLACK_EMAIL_DEFAULT_ACTION = "🔔 Has updates"

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
        SLACK_ACTION_ADVANCE_ROLLOUT_PHASE_REQUEST: (
            NimbusConstants.AlertType.UPDATE_REQUEST
        ),
        SLACK_ACTION_DISABLE_ROLLOUT_REQUEST: (
            NimbusConstants.AlertType.END_EXPERIMENT_REQUEST
        ),
        SLACK_ACTION_REENABLE_ROLLOUT_REQUEST: (NimbusConstants.AlertType.LAUNCH_REQUEST),
    }

    # Slack emoji reaction names
    class EmojiReaction:
        PENDING = "question"
        CANCEL = "x"
        APPROVE = "eyes"
        COMPLETE = "white_check_mark"
        SECURE = "lock"

    # Slack API error codes
    class ErrorCode:
        ALREADY_REACTED = "already_reacted"
        NO_REACTION = "no_reaction"

    # Enrollment monitoring thresholds
    UNENROLLMENT_SPIKE_THRESHOLD = 0.10  # 10%
    SRM_MISMATCH_P_VALUE_THRESHOLD = 0.001  # p < 0.001

    # Slack message templates
    SLACK_DM_PREFIX = "🔔 Join {channel} to get slack notifications: {message}"
    SLACK_DM_CHANNEL_LINK_SUFFIX = "\n\n🔗 View in channel: {channel_message_link}"
    SLACK_LAUNCH_SUCCESS_MESSAGE = "🚀 ✅ Launched"
    SLACK_UPDATE_SUCCESS_MESSAGE = "🔄 ✅ Published update"
    SLACK_ENROLLMENT_ENDED_MESSAGE = "⏸️ ✅ Ended enrollment"
    SLACK_EXPERIMENT_ENDED_MESSAGE = "🛑 ✅ Ended experiment"
    SLACK_ROLLOUT_PHASE_ADVANCED_MESSAGE = "⏩ ✅ Advanced rollout phase"
    SLACK_ROLLOUT_DISABLED_MESSAGE = "⏸️ ✅ Disabled rollout"
    SLACK_ROLLOUT_REENABLED_MESSAGE = "▶️ ✅ Re-enabled rollout"
    SLACK_RESULTS_READY_MESSAGE = "📈 {window} results ready"
    SLACK_ANALYSIS_ERRORS_ACTION = "⚠️ Analysis errors"
    SLACK_UNENROLLMENT_SPIKE_ACTION = "⚠️ Unenrollment spike"
    SLACK_UNENROLLMENT_SPIKE_DETAILS = (
        "Unenrollment rate {rate:.1%} after {days} days (threshold {threshold:.1%})\n"
        "Primary reason: {reason}"
    )
    SLACK_SRM_MISMATCH_ACTION = "⚠️ Branch ratio mismatch"
    SLACK_SRM_MISMATCH_DETAILS = (
        "Enrollment is not at the expected ratio across branches. "
        "Please review the results."
    )
    SLACK_ZERO_ENROLLMENT_ACTION = "⚠️ Low enrollment"
    SLACK_ZERO_ENROLLMENT_DETAILS = (
        "Fewer than {client_threshold:,} clients enrolled after {days} days "
        "(current: {total_enrollments:,}).\n"
        "Please review targeting, percentage, and feature conflicts."
    )
    SLACK_NOT_UNENROLLING_ACTION = "⚠️ Clients not unenrolling"
    SLACK_NOT_UNENROLLING_DETAILS = (
        "Ended {days} days ago and fewer than {client_threshold:,} clients have "
        "unenrolled (current: {unenrollments:,}).\n"
        "Recipe deletions may not be reaching clients. Please report in #nimbus-help."
    )
    SLACK_FEATURE_CONFLICT_ACTION = "⚠️ Feature conflict"
    SLACK_FEATURE_CONFLICT_DETAILS = (
        "Affects {rate:.1%} of the evaluated population.\n"
        "Blocking recipe: {conflict_slugs}"
    )

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
    SLACK_LOG_ROLLOUT_PHASE_ADVANCE_SENT = (
        "Sent rollout phase advance success notification for {experiment}"
    )
    SLACK_LOG_ROLLOUT_DISABLE_SENT = (
        "Sent rollout disable success notification for {experiment}"
    )
    SLACK_LOG_ROLLOUT_REENABLE_SENT = (
        "Sent rollout re-enable success notification for {experiment}"
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
    SLACK_LOG_EMOJI_ALREADY_REMOVED = (
        "{emoji_name} emoji already removed or never existed for {experiment}"
    )
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
    SLACK_LOG_UNENROLLMENT_SPIKE_SENT = (
        "Sent unenrollment spike alert for experiment {experiment}"
    )
    SLACK_LOG_SRM_MISMATCH_SENT = "Sent SRM mismatch alert for experiment {experiment}"
    SLACK_LOG_ZERO_ENROLLMENT_SENT = (
        "Sent zero enrollment alert for experiment {experiment}"
    )
    SLACK_LOG_FAILED_SEND_UNENROLLMENT_SPIKE = (
        "Failed to send unenrollment spike alert for experiment {experiment}"
    )
    SLACK_LOG_FAILED_SEND_SRM_MISMATCH = (
        "Failed to send SRM mismatch alert for experiment {experiment}"
    )
    SLACK_LOG_FAILED_SEND_ZERO_ENROLLMENT = (
        "Failed to send zero enrollment alert for experiment {experiment}"
    )
    SLACK_LOG_NOT_UNENROLLING_SENT = (
        "Sent not unenrolling alert for experiment {experiment}"
    )
    SLACK_LOG_FAILED_SEND_NOT_UNENROLLING = (
        "Failed to send not unenrolling alert for experiment {experiment}"
    )
    SLACK_LOG_FEATURE_CONFLICT_SENT = (
        "Sent feature conflict alert for experiment {experiment}"
    )
    SLACK_LOG_FAILED_SEND_FEATURE_CONFLICT = (
        "Failed to send feature conflict alert for experiment {experiment}"
    )
    SLACK_LOG_MONITORING_ALERTS_ERROR = (
        "Error checking monitoring alerts for experiment {experiment}"
    )
    SLACK_LOG_NOTIFICATION_TASK_SENT = (
        "Slack notification sent for experiment {experiment_id}"
    )
    SLACK_LOG_NOTIFICATION_TASK_FAILED = (
        "Sending Slack notification for experiment {experiment_id} failed"
    )
    SLACK_LOG_ERROR_ADDING_EMOJI = (
        "Error adding {emoji_name} emoji to message for experiment {experiment_id}"
    )
