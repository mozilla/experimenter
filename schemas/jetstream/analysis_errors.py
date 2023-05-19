import datetime as dt
from pydantic import BaseModel
from typing import Optional

from .statistics import AnalysisBasis


class AnalysisError(BaseModel):
    analysis_basis: Optional[AnalysisBasis] = None
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


class AnalysisErrors(BaseModel):
    __root__: list[AnalysisError]
