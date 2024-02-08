from enum import Enum
from typing import Optional

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Field, root_validator

SCHEMA_VERSION = 4


class AnalysisBasis(str, Enum):
    ENROLLMENTS = "enrollments"
    EXPOSURES = "exposures"


class Statistic(BaseModel):
    metric: str
    statistic: str
    branch: str
    parameter: Optional[float] = None
    comparison: Optional[str] = None
    comparison_to_branch: Optional[str] = None
    ci_width: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    point: Optional[float] = None
    lower: Optional[float] = None
    upper: Optional[float] = None
    p_value: Optional[float] = None
    segment: str = Field(default="all")
    analysis_basis: Optional[AnalysisBasis]
    window_index: Optional[str]


class Statistics(BaseModel):
    __root__: list[Statistic]

    @root_validator
    def check_for_duplicates(cls, v):
        if "__root__" in v:
            dupes_by_metadata = {}
            for stat in v["__root__"]:
                meta = (
                    stat.metric,
                    stat.statistic,
                    stat.branch,
                    stat.parameter,
                    stat.comparison,
                    stat.comparison_to_branch,
                    stat.ci_width,
                    stat.segment,
                    stat.analysis_basis,
                    stat.window_index,
                )
                if dupes_by_metadata.get(meta):
                    raise ValueError("List of Statistic objects has duplicate(s).")

                dupes_by_metadata[meta] = True

        return v


class StatisticsFactory(ModelFactory[Statistics]):
    __model__ = Statistics
