from enum import Enum


class NimbusUIConstants:
    HYPOTHESIS_PLACEHOLDER = """
Hypothesis: If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.

We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>

    """.strip()  # noqa: E501

    ERROR_NAME_INVALID = "This is not a valid name."
    ERROR_SLUG_DUPLICATE = "An experiment with this slug already exists."
    ERROR_SLUG_DUPLICATE_BRANCH = "A branch with this slug already exists."

    ERROR_HYPOTHESIS_PLACEHOLDER = "Please enter a hypothesis."
    ERROR_NAME_MAPS_TO_EXISTING_SLUG = (
        "Name maps to a pre-existing slug, please choose another name."
    )
    ERROR_TAG_DUPLICATE_NAME = "Tag with this Name already exists."

    RISK_MESSAGE_URL = "https://mozilla-hub.atlassian.net/wiki/spaces/FIREFOX/pages/208308555/Message+Consult+Creation"
    REVIEW_URL = "https://experimenter.info/access"

    EXCLUDING_EXPERIMENTS_WARNING = """The following experiments are being excluded by
    your experiment and may reduce the eligible population for your experiment which
    may result in reduced statistical power and precision. Please check that the
    configured population proportion has accounted for this:"""
    LIVE_EXPERIMENTS_BUCKET_WARNING = """The following experiments are LIVE on a
    previous namespace and may reduce the eligible population for your experiment
    which may result in reduced statistical power and precision. Please check that
    the configured population proportion has accounted for this:"""
    LIVE_MULTIFEATURE_WARNING = """The following multi-feature experiments are LIVE
    and may reduce the eligible population for your experiment which may result in
    reduced statistical power and precision. Please check that the configured population
    proportion has accounted for this:"""
    ERROR_ROLLOUT_BUCKET_EXISTS = """WARNING: A rollout already exists for this
    combination of application, feature, channel, and advanced targeting!
        If this rollout is launched, a client meeting the advanced
        targeting criteria will be enrolled in one and not the other and
        you will not be able to adjust the sizing for this rollout."""
    PREF_TARGETING_WARNING = """WARNING: The following rollouts are LIVE
    that set the same prefs and may reduce the eligible population for your experiment
    which may result in reduced statistical power and precision or prevent enrollment
    entirely. Please check that the configured population proportion has accounted for
    this:"""
    EXPERIMENT_MULTICHANNEL_WARNING = """WARNING: This experiment is targeting multiple
    channels.  Each channel has significantly different population sizes and user
    behaviour.  Running an experiment on multiple channels can create misleading or
    inaccurate results.  It is recommended to run experiments only on a single channel."""

    AUDIENCE_OVERLAP_WARNING = "https://experimenter.info/faq/warnings/#audience-overlap"
    ROLLOUT_BUCKET_WARNING = (
        "https://experimenter.info/faq/warnings/#rollout-bucketing-warning"
    )
    TARGETING_CRITERIA_REQUEST_INFO = """If the option you need is not in the advanced
    targeting list - file a new targeting request with this link, and share the created
    request with either your feature engineering team or in #ask-experimenter
    so the new targeting can be added."""
    TIMELINE_TOOLTIPS = {
        "Draft": (
            "The duration from the initial draft of the experiment to its entry "
            "into either the preview or review stage."
        ),
        "Preview": ("The number of days the experiment has spent in the preview stage."),
        "Review": ("The number of days the experiment has spent in the review stage."),
        "Enrollment": (
            "The duration from the start to the end of the participant enrollment period."
        ),
        "Complete": (
            "The total number of days from the start of participant enrollment "
            "to the end of the experiment."
        ),
        "Observation": (
            "The number of days the experiment was observed after the enrollment "
            "period ended."
        ),
    }
    EXPERIMENT_ORDERING = {
        "Draft": 1,
        "Preview": 2,
        "Review": 3,
        "Enrollment": 4,
        "Observation": 5,
        "Complete": 6,
    }
    HOME_PAGE_LINKS = {
        "welcome_learn_more_url": "https://experimenter.info/workflow/overview/"
    }
    AUDIENCE_PAGE_LINKS = {
        "custom_audiences_url": "https://experimenter.info/workflow/implementing/custom-audiences#how-to-add-a-new-custom-audience",
        "targeting_criteria_request_url": "https://github.com/mozilla/experimenter/issues/new?template=targeting_request_template.yml&title=Targeting%20criteria%20request",
        "sticky_targeting_url": "https://experimenter.info/workflow/implementing/custom-audiences#sticky-targeting",
        "experimentation_office_hours_url": "https://mozilla-hub.atlassian.net/wiki/spaces/DATA/pages/6849684/Experimentation+Office+Hours",
    }
    OVERVIEW_PAGE_LINKS = {
        "risk_link": "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-Doesthishavehighrisktothebrand?",
        "message_consult_link": "https://mozilla-hub.atlassian.net/wiki/spaces/FIREFOX/pages/208308555/Message+Consult+Creation",
        "revenue_risk_link": "https://experimenter.info/vp-sign-off",
        "partner_related_risk_link": "https://experimenter.info/legal-sign-off",
    }
    METRICS_PAGE_LINKS = {
        "metrics_hub_url": "https://mozilla.github.io/metric-hub/metrics/firefox_desktop/",
        "segment_metrics_hub_url": "https://mozilla.github.io/metric-hub/segments/firefox_desktop/",
    }
    HOME_PAGE_TOOLTIPS = {
        "draft_or_preview": """This is anything that you own or are subscribed
            to follow - which are in Draft or Preview states. Go to the link to
            check the message for the next actions needed.
        """,
        "ready_for_attention": """This is anything that you own or are subscribed to
            follow when they are in a Review state; have a change due for ending
            enrollment or ending entirely; or have ended and have no information in
            the take-aways section.
        """,
        "my_deliveries": """
            Shows all deliveries (experiments, rollouts, etc) that you are the owner of,
            subscribed to or where you are a collaborator.
            <a href="https://experimenter.info/for-product">Learn</a> how to get started.
        """,
    }
    SIDEBAR_COMMON_LINKS = {
        "Performance Reports": {
            "url": "https://protosaur.dev/perf-reports/",
            "tooltip": """Performance Reports are only created for experiments that have
            ended.""",
            "icon": "fa-solid fa-chart-line",
        },
        "Messaging Skylight": {
            "url": "https://fxms-skylight.netlify.app/complete#complete_experiments",
            "tooltip": """Messaging Skylight takes you to Skylight - the messaging team's
            tool to show message interaction details.""",
            "icon": "fa-solid fa-envelope-open-text",
        },
    }
    LIVE_MONITOR_TOOLTIP = """Live Monitoring shows enrollment/unenrollment for this
    delivery"""

    OVERVIEW_SECTIONS = [
        "Hypothesis",
        "Branch overview",
        "Key takeaways",
        "Next steps",
        "Project impact",
    ]
    KPI_AREA = "KPI Metrics"
    OTHER_METRICS_AREA = "Other Metrics"
    NOTABLE_METRIC_AREA = "Notable Changes"
    NOTABLE_METRIC_AREA_SUBHEADER = (
        "All statistically significant changes that have occurred in the experiment"
    )
    FEATURE_PAGE_LINKS = {
        "feature_learn_more_url": "https://experimenter.info/for-product#track-your-feature-health",
        "deliveries_table_tooltip": """This shows all Nimbus experiments, rollouts, Labs
        experiences, etc. associated with your selected feature.""",
    }

    FEATURE_PAGE_TOOLTIPS = {
        "feature_changes_tooltip": """This shows any changes made to the Nimbus feature
        manifest such as code changes for the feature you have chosen.""",
        "subscribe_tooltip": """Subscribe to {text} to get email notifications
        when deliveries use this feature as well as show deliveries that use
        this feature on your Home view.""",
        "unsubscribe_tooltip": """Unsubscribe from {text} to stop email
        notifications for changes to this feature's configuration or deliveries
        and remove them from your Home view.""",
    }

    OVERVIEW_REFLECTION_PROMPTS = {
        "key_takeaways": """Highlight the most important learnings or patterns from this
        experiment.""",
        "next_steps": """Outline what should happen next based on these results — fixes,
        follow-ups, or future tests.""",
        "project_impact": """Set an impact rating so others can understand the scale of
        this experiment's effect.""",
    }
    COENROLLMENT_NOTE = (
        "Note: This feature supports co-enrollment with other experiments/rollouts "
        "for the selected versions."
    )

    class ReviewRequestMessages(Enum):
        END_EXPERIMENT = "end this experiment"
        END_ENROLLMENT = "end enrollment for this experiment"
        LAUNCH_EXPERIMENT = "launch this experiment"
        LAUNCH_ROLLOUT = "launch this rollout"
        UPDATE_ROLLOUT = "update this rollout"
        END_ROLLOUT = "end this rollout"


def _get_qa_status_icon_map():
    from experimenter.experiments.constants import NimbusConstants

    return {
        NimbusConstants.QAStatus.NOT_SET: {
            "icon": "fa-regular fa-circle-question",
            "color": "",
        },
        NimbusConstants.QAStatus.GREEN: {
            "icon": "fa-regular fa-circle-check",
            "color": "text-success",
        },
        NimbusConstants.QAStatus.SELF_GREEN: {
            "icon": "fa-solid fa-check",
            "color": "text-success",
        },
        NimbusConstants.QAStatus.YELLOW: {
            "icon": "fa-regular fa-circle-pause",
            "color": "text-warning",
        },
        NimbusConstants.QAStatus.SELF_YELLOW: {
            "icon": "fa-regular fa-circle-pause",
            "color": "text-warning",
        },
        NimbusConstants.QAStatus.RED: {
            "icon": "fa-regular fa-circle-xmark",
            "color": "text-danger",
        },
        NimbusConstants.QAStatus.SELF_RED: {
            "icon": "fa-regular fa-circle-xmark",
            "color": "text-danger",
        },
    }


def _get_channel_icon_map():
    from experimenter.experiments.constants import NimbusConstants

    return {
        NimbusConstants.Channel.NO_CHANNEL: {
            "icon": "fa-regular fa-circle-question",
            "color": "text-muted",
        },
        NimbusConstants.Channel.UNBRANDED: {
            "icon": "fa-solid fa-globe",
            "color": "text-secondary",
        },
        NimbusConstants.Channel.NIGHTLY: {
            "icon": "fa-brands fa-firefox",
            "color": "text-info",
        },
        NimbusConstants.Channel.BETA: {
            "icon": "fa-brands fa-firefox",
            "color": "text-primary",
        },
        NimbusConstants.Channel.RELEASE: {
            "icon": "fa-brands fa-firefox",
            "color": "text-success",
        },
        NimbusConstants.Channel.ESR: {
            "icon": "fa-brands fa-firefox",
            "color": "text-info",
        },
        NimbusConstants.Channel.TESTFLIGHT: {
            "icon": "fa-solid fa-plane",
            "color": "text-primary",
        },
        NimbusConstants.Channel.AURORA: {
            "icon": "fa-solid fa-bolt",
            "color": "text-warning",
        },
        NimbusConstants.Channel.DEVELOPER: {
            "icon": "fa-solid fa-code",
            "color": "text-secondary",
        },
        NimbusConstants.Channel.STAGING: {
            "icon": "fa-solid fa-cog",
            "color": "text-muted",
        },
        NimbusConstants.Channel.PRODUCTION: {
            "icon": "fa-solid fa-star",
            "color": "text-success",
        },
    }


def _get_application_icon_map():
    from experimenter.experiments.constants import NimbusConstants

    return {
        NimbusConstants.Application.DESKTOP: {
            "icon": "fa-fw fa-solid fa-computer",
            "color": "text-primary",
        },
        NimbusConstants.Application.FENIX: {
            "icon": "fa-fw fa-brands fa-android",
            "color": "text-success",
        },
        NimbusConstants.Application.IOS: {
            "icon": "fa-fw fa-brands fa-apple",
            "color": "text-secondary",
        },
        NimbusConstants.Application.FOCUS_ANDROID: {
            "icon": "fa-fw fa-brands fa-android",
            "color": "text-success",
        },
        NimbusConstants.Application.KLAR_ANDROID: {
            "icon": "fa-fw fa-brands fa-android",
            "color": "text-success",
        },
        NimbusConstants.Application.FOCUS_IOS: {
            "icon": "fa-fw fa-brands fa-apple",
            "color": "text-secondary",
        },
        NimbusConstants.Application.KLAR_IOS: {
            "icon": "fa-fw fa-brands fa-apple",
            "color": "text-secondary",
        },
        NimbusConstants.Application.MONITOR: {
            "icon": "fa-fw fa-solid fa-shield-alt",
            "color": "text-info",
        },
        NimbusConstants.Application.VPN: {
            "icon": "fa-fw fa-solid fa-user-shield",
            "color": "text-warning",
        },
        NimbusConstants.Application.FXA: {
            "icon": "fa-fw fa-solid fa-user-circle",
            "color": "text-primary",
        },
        NimbusConstants.Application.DEMO_APP: {
            "icon": "fa-fw fa-solid fa-flask",
            "color": "text-danger",
        },
        NimbusConstants.Application.EXPERIMENTER: {
            "icon": "fa-fw fa-solid fa-vial",
            "color": "text-purple",
        },
    }


def _get_status_icon_map():
    from experimenter.experiments.constants import NimbusConstants

    return {
        NimbusConstants.Status.DRAFT: {
            "icon": "fa-regular fa-file-lines",
            "color": "text-muted",
        },
        NimbusConstants.Status.PREVIEW: {
            "icon": "fa-regular fa-eye",
            "color": "text-info",
        },
        NimbusConstants.Status.LIVE: {
            "icon": "fa-solid fa-play",
            "color": "text-success",
        },
        NimbusConstants.Status.COMPLETE: {
            "icon": "fa-solid fa-flag-checkered",
            "color": "text-primary",
        },
        NimbusConstants.PublishStatus.REVIEW: {
            "icon": "fa-regular fa-hourglass-half",
            "color": "text-warning",
        },
    }


def _get_schema_diff_size_config():
    return {
        "thresholds": {
            "small": 3,
            "medium": 10,
        },
        "labels": {
            "no_changes": {
                "text": "No Changes",
                "badge_class": "badge bg-success",
            },
            "small": {
                "text": "Small",
                "badge_class": "badge bg-primary",
            },
            "medium": {
                "text": "Medium",
                "badge_class": "badge bg-warning",
            },
            "large": {
                "text": "Large",
                "badge_class": "badge bg-danger",
            },
            "first_version": {
                "text": "First Version",
                "badge_class": "badge bg-secondary",
            },
        },
    }


QA_STATUS_ICON_MAP = _get_qa_status_icon_map()
CHANNEL_ICON_MAP = _get_channel_icon_map()
APPLICATION_ICON_MAP = _get_application_icon_map()
STATUS_ICON_MAP = _get_status_icon_map()
SCHEMA_DIFF_SIZE_CONFIG = _get_schema_diff_size_config()

# Icon filter type constants for template tags
QA_ICON_FILTER_TYPE = "qa_icon_info"
CHANNEL_ICON_FILTER_TYPE = "channel_icon_info"
APPLICATION_ICON_FILTER_TYPE = "application_icon_info"
STATUS_ICON_FILTER_TYPE = "status_icon_info"
