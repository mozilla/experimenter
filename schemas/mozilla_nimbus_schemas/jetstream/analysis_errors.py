import datetime as dt
from enum import Enum
from typing import Optional

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, RootModel

from mozilla_nimbus_schemas.jetstream.statistics import AnalysisBasis


class LogSource(str, Enum):
    JETSTREAM = "jetstream"
    SIZING = "sizing"
    PREVIEW = "jetstream-preview"


class AnalysisError(BaseModel):
    analysis_basis: Optional[AnalysisBasis] = None
    source: Optional[LogSource] = None
    exception: Optional[str] = None
    exception_type: Optional[str] = None
    experiment: Optional[str] = None
    filename: str
    func_name: str
    log_level: str
    message: str
    metric: Optional[str] = None
    segment: Optional[str] = None
    statistic: Optional[str] = None
    timestamp: dt.datetime


class AnalysisErrors(RootModel):
    root: list[AnalysisError]


class AnalysisErrorsFactory(ModelFactory[AnalysisErrors]):
    __model__ = AnalysisErrors
