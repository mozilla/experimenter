from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AnalysisBasis(str, Enum):
    enrollments = "enrollments"
    exposures = "exposures"


class Statistic(BaseModel):
    metric: str
    statistic: str
    branch: str
    comparison: Optional[str] = None
    comparison_to_branch: Optional[str] = None
    ci_width: float = Field(default=None, ge=0.0, le=1.0)
    point: float
    lower: Optional[float] = None
    upper: Optional[float] = None
    segment: str = Field(default="all")
    analysis_basis: AnalysisBasis
    window_index: str


class Statistics(BaseModel):
    __root__: list[Statistic]
