class NimbusUIConstants:
    HYPOTHESIS_PLACEHOLDER = """
Hypothesis: If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.

We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>

    """.strip()  # noqa: E501

    ERROR_NAME_INVALID = "This is not a valid name."
    ERROR_SLUG_DUPLICATE = "An experiment with this slug already exists."
    ERROR_HYPOTHESIS_PLACEHOLDER = "Please enter a hypothesis."

    RISK_MESSAGE_URL = "https://mozilla-hub.atlassian.net/wiki/spaces/FIREFOX/pages/208308555/Message+Consult+Creation"

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

    AUDIENCE_OVERLAP_WARNING = "https://experimenter.info/faq/warnings/#audience-overlap"
    TARGETING_CRITERIA_REQUEST = (
        "https://github.com/mozilla-extensions/nimbus-devtools/issues/new"
        "?title=Targeting%20criteria%20request"
        "&body=*%20What%20is%20the%20criteria%20you%20need%20to%20target%20based%20on%3F%20Be%20specific.%0A"
        "Ex%3A%20if%20targeting%20based%20on%20a%20preference%2C%20what%20is%20the%20preference%20name%20and%20what%20state%20should%20it%20be%3F%20%0A"
        "Ex%3A%20if%20you%20need%20to%20target%20only%20Windows%20users%2C%20is%20there%20a%20minimum%20version%3F%0A%0A"
        "*%20Do%20you%20need%20to%20include%20or%20exclude%20users%20based%20on%20the%20criteria%20you%20described"
    )
    CUSTOM_AUDIENCES = "https://experimenter.info/workflow/implementing/custom-audiences#how-to-add-a-new-custom-audience"
    TARGETING_CRITERIA_REQUEST_INFO = """If the option you need is not in the advanced
    targeting list - file a new targeting request with this link, and share the created request with either
    your feature engineering team or in #ask-experimenter so the new targeting can be added."""
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
        ],
    }
