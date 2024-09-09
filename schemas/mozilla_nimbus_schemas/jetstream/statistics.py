from enum import Enum
from typing import Optional

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Field, RootModel, model_validator

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
    segment: str = Field(default="all")
    analysis_basis: Optional[AnalysisBasis] = None
    window_index: Optional[str] = None


class Statistics(RootModel):
    root: list[Statistic]

    @model_validator(mode="after")
    def check_for_duplicates(self):
        if "root" in self:
            dupes_by_metadata = {}
            for stat in self.root:
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

        return self


class StatisticsFactory(ModelFactory[Statistics]):
    __model__ = Statistics
