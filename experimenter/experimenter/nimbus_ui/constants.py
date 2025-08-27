from enum import Enum


class NimbusUIConstants:
    HYPOTHESIS_PLACEHOLDER = """
Hypothesis: If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.

We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>

    """.strip()  # noqa: E501

    ERROR_NAME_INVALID = "This is not a valid name."
    ERROR_SLUG_DUPLICATE = "An experiment with this slug already exists."
    ERROR_HYPOTHESIS_PLACEHOLDER = "Please enter a hypothesis."
    ERROR_NAME_MAPS_TO_EXISTING_SLUG = (
        "Name maps to a pre-existing slug, please choose another name."
    )

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

    AUDIENCE_OVERLAP_WARNING = "https://experimenter.info/faq/warnings/#audience-overlap"
    ROLLOUT_BUCKET_WARNING = (
        "https://experimenter.info/faq/warnings/#rollout-bucketing-warning"
    )
    TARGETING_CRITERIA_REQUEST = (
        "https://github.com/mozilla/experimenter/issues/new"
        "?template=targeting_request_template.yml"
        "&title=Targeting%20criteria%20request"
    )
    CUSTOM_AUDIENCES = "https://experimenter.info/workflow/implementing/custom-audiences#how-to-add-a-new-custom-audience"
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
    HOME_PAGE_LINKS = {
        "welcome_learn_more_url": "https://experimenter.info/workflow/overview/"
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
    # TODO: Add learn more URL for feature page (EXP-5876)
    FEATURE_PAGE_LINKS = {"feature_learn_more_url": ""}

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


QA_STATUS_ICON_MAP = _get_qa_status_icon_map()
CHANNEL_ICON_MAP = _get_channel_icon_map()

# Icon filter type constants for template tags
QA_ICON_FILTER_TYPE = "qa_icon_info"
CHANNEL_ICON_FILTER_TYPE = "channel_icon_info"
