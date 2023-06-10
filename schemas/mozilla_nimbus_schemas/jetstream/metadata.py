import datetime as dt
import json
from typing import Optional

from pydantic import BaseModel, HttpUrl

from mozilla_nimbus_schemas.jetstream.statistics import AnalysisBasis


def nonstrict_json_loads(*args, **kwargs):
    kwargs.update({"strict": False})
    return json.loads(*args, **kwargs)


class Metric(BaseModel):
    analysis_bases: list[AnalysisBasis]
    bigger_is_better: bool
    description: Optional[str] = None
    friendly_name: Optional[str] = None

    class Config:
        # override json_loads because `description` field may contain \n
        json_loads = nonstrict_json_loads


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
    url: HttpUrl


class Metadata(BaseModel):
    analysis_start_time: Optional[dt.datetime] = None
    external_config: Optional[ExternalConfig] = None
    metrics: dict[str, Metric]
    outcomes: dict[str, Outcome] = {}
    schema_version: int

    class Config:
        # override json_loads because `description` field in Metric may contain \n
        json_loads = nonstrict_json_loads
