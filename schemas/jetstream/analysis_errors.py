import datetime as dt
from pydantic import BaseModel

from .statistics import AnalysisBasis


class AnalysisError(BaseModel):
    analysis_basis: AnalysisBasis = None
    exception: str
    exception_type: str
    experiment: str
    filename: str
    func_name: str
    log_level: str
    message: str
    metric: str
    segment: str
    statistic: str
    timestamp: dt.datetime


class AnalysisErrors(BaseModel):
    __root__: list[AnalysisError]
