import datetime as dt
from typing import Optional

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, HttpUrl, field_validator

from mozilla_nimbus_schemas.jetstream.statistics import SCHEMA_VERSION, AnalysisBasis


class Metric(BaseModel):
    analysis_bases: list[AnalysisBasis]
    bigger_is_better: bool
    description: Optional[str] = None
    friendly_name: Optional[str] = None


class Outcome(BaseModel):
    commit_hash: Optional[str] = None
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


class ConfigVersionDetails(BaseModel):
    path: Optional[str] = None
    revision: Optional[str] = None


class ConfigVersions(BaseModel):
    metric_definitions: Optional[list[ConfigVersionDetails]] = None
    jetstream_image: Optional[ConfigVersionDetails] = None


class Metadata(BaseModel):
    analysis_start_time: Optional[dt.datetime] = None
    external_config: Optional[ExternalConfig] = None
    metrics: dict[str, Metric]
    outcomes: dict[str, Outcome] = {}
    version_info: Optional[ConfigVersions] = None
    version_date: Optional[dt.datetime] = None
    schema_version: int = SCHEMA_VERSION

    @field_validator("analysis_start_time", mode="before")
    @classmethod
    def treat_empty_str_as_none(cls, v):
        return None if v == "" else v


class MetadataFactory(ModelFactory[Metadata]):
    __model__ = Metadata
