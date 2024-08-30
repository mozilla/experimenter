from enum import Enum


class StrEnum(str, Enum):
    """This replicates the behavior of StrEnum from Python 3.11.

    TODO: replace with `StrEnum` from enum package in Python 3.11+
    """

    def __str__(self) -> str:
        return self.value


class AnalysisSegment(StrEnum):
    ALL = "all"


class AnalysisSignificance(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AnalysisWindow(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    OVERALL = "overall"


class BranchComparison(StrEnum):
    ABSOLUTE = "absolute"
    DIFFERENCE = "difference"
    UPLIFT = "relative_uplift"


# TODO: Consider a "guardrail_metrics" group containing "days_of_use",
# "retained", and "search_count".
class MetricGroup(StrEnum):
    SEARCH = "search_metrics"
    USAGE = "usage_metrics"
    OTHER = "other_metrics"


class MetricIngestEnum(StrEnum):
    RETENTION = "retained"
    SEARCH = "search_count"
    DAYS_OF_USE = "days_of_use"
    USER_COUNT = "identity"


class StatisticIngestEnum(StrEnum):
    """
    This is the list of statistics supported in Experimenter,
    not a complete list of statistics available in Jetstream.
    """

    PERCENT = "percentage"
    BINOMIAL = "binomial"
    MEAN = "mean"
    COUNT = "count"
