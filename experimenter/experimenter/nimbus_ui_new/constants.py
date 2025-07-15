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

    class ReviewRequestMessages(Enum):
        END_EXPERIMENT = "end this experiment"
        END_ENROLLMENT = "end enrollment for this experiment"
        LAUNCH_EXPERIMENT = "launch this experiment"
        LAUNCH_ROLLOUT = "launch this rollout"
        UPDATE_ROLLOUT = "update this rollout"
        END_ROLLOUT = "end this rollout"

    FIELD_PAGE_MAP = {
        "overview": [
            "projects",
            "public_description",
            "risk_brand",
            "risk_message",
            "risk_revenue",
            "risk_partner_related",
        ],
        "branches": [
            "reference_branch",
            "treatment_branches",
            "feature_configs",
            "is_rollout",
            "localizations",
        ],
        "audience": [
            "channel",
            "firefox_min_version",
            "languages",
            "locales",
            "countries",
            "targeting_config_slug",
            "proposed_enrollment",
            "proposed_duration",
            "population_percent",
            "total_enrolled_clients",
            "required_experiments_branches",
            "excluded_experiments_branches",
            "is_sticky",
        ],
    }
