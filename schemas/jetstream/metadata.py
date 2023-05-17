import datetime as dt
from pydantic import BaseModel

from .statistics import AnalysisBasis


class Metric(BaseModel):
    analysis_bases: list(AnalysisBasis)
    bigger_is_better: bool
    description: str
    friendly_name: str


class Outcome(BaseModel):
    commit_hash: str
    default_metrics: list[str]
    description: str
    friendly_name: str
    metrics: list[str]
    slug: str


class ExternalConfig(BaseModel):
    reference_branch: str = None
    end_date: dt.date = None
    start_date: dt.date = None
    enrollment_period: int = None
    skip: bool = None
    url: str


class Metadata(BaseModel):
    analysis_start_time: dt.datetime
    external_config: str
    metrics: dict[str, Metric]
    outcomes: dict[str, Outcome]
    schema_version: int
