import datetime as dt
from pydantic import BaseModel
from typing import Optional

from .statistics import AnalysisBasis


class Metric(BaseModel):
    analysis_bases: list(AnalysisBasis)
    bigger_is_better: bool
    description: Optional[str] = None
    friendly_name: Optional[str] = None


class Outcome(BaseModel):
    commit_hash: str
    default_metrics: list[str]
    description: str
    friendly_name: str
    metrics: list[str]
    slug: str


class ExternalConfig(BaseModel):
    reference_branch: Optional[str] = None
    end_date: Optional[dt.date] = None
    start_date: Optional[dt.date] = None
    enrollment_period: Optional[int] = None
    skip: Optional[bool] = None
    url: str


class Metadata(BaseModel):
    analysis_start_time: Optional[dt.datetime] = None
    external_config: Optional[ExternalConfig] = None
    metrics: dict[str, Metric]
    outcomes: dict[str, Outcome] = {}
    schema_version: int
