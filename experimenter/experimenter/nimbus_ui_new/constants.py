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

    TIMELINE_TOOLTIPS = {
        "Draft": (
            "The number of days between when the experiment was first drafted "
            "and when it moved to either the preview stage or the review stage."
        ),
        "Preview": (
            "The number of days the experiment remained in the preview phase "
            "before it was reviewed."
        ),
        "Review": (
            "The number of days from when the experiment was reviewed to when "
            "participant enrollment began."
        ),
        "Enrollment": (
            "The number of days from when the experiment began enrolling participants "
            "to when the enrollment period ended."
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
