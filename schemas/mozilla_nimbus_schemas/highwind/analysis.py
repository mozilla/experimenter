import datetime as dt
from enum import Enum

from pydantic import BaseModel, ConfigDict


class HighwindModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HighwindAnalysisUnit(str, Enum):
    CLIENT_ID = "client_id"
    PROFILE_GROUP_ID = "profile_group_id"


class HighwindLogLevel(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"


class HighwindWindowKind(str, Enum):
    CUMULATIVE = "cumulative"
    DISJOINT = "disjoint"


class HighwindCellState(str, Enum):
    NOT_STARTED = "not_started"
    INSUFFICIENT_DATA = "insufficient_data"
    FORMING = "forming"
    CONFIDENT = "confident"
    ERROR = "error"


class HighwindDirection(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class HighwindWindow(HighwindModel):
    kind: HighwindWindowKind
    start_day: int
    end_day: int
    matures_on: dt.date | None


class HighwindInterval(HighwindModel):
    point: float | None
    lower: float | None
    upper: float | None


class HighwindBranchValue(HighwindModel):
    branch: str
    n: int
    value: HighwindInterval


class HighwindComparison(HighwindModel):
    branch: str
    reference_branch: str
    state: HighwindCellState
    direction: HighwindDirection
    relative: HighwindInterval
    absolute: HighwindInterval
    n_reference: int | None
    n_treatment: int | None
    error: str | None


class HighwindWindowResult(HighwindModel):
    window: HighwindWindow
    is_summary: bool
    branches: list[HighwindBranchValue]
    comparisons: list[HighwindComparison]


class HighwindSegmentResult(HighwindModel):
    segment: str
    windows: list[HighwindWindowResult]


class HighwindMetricResult(HighwindModel):
    slug: str
    friendly_name: str
    description: str | None = None
    segments: list[HighwindSegmentResult]


class HighwindSegmentBranch(HighwindModel):
    branch: str
    units: int


class HighwindSegment(HighwindModel):
    slug: str
    friendly_name: str
    description: str | None = None
    branches: list[HighwindSegmentBranch]


class HighwindMetadata(HighwindModel):
    schema_version: int
    experiment_slug: str
    as_of_date: dt.date
    generated_at: dt.datetime
    pipeline_version: str
    start_date: dt.date
    end_date: dt.date | None
    analysis_unit: HighwindAnalysisUnit
    reference_branch: str
    branches: list[str]


class HighwindError(HighwindModel):
    timestamp: dt.datetime
    log_level: HighwindLogLevel
    message: str
    exception_type: str | None
    exception: str | None
    filename: str
    func_name: str
    metric: str | None
    segment: str | None
    window: HighwindWindow | None


class HighwindAnalysis(HighwindModel):
    metadata: HighwindMetadata
    segments: list[HighwindSegment]
    metrics: list[HighwindMetricResult]
    errors: list[HighwindError]
