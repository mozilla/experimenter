from enum import Enum
from typing import Optional

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, RootModel


class SizingMetricName(str, Enum):
    ACTIVE_HOURS = "active_hours"
    SEARCH_COUNT = "search_count"
    DAYS_OF_USE = "days_of_use"
    TAGGED_SEARCH_COUNT = "tagged_search_count"


class SizingReleaseChannel(str, Enum):
    RELEASE = "release"
    BETA = "beta"
    NIGHTLY = "nightly"


class SizingUserType(str, Enum):
    NEW = "new"
    EXISTING = "existing"
    ALL = "all"


class SizingMetric(BaseModel):
    number_of_clients_targeted: int
    sample_size_per_branch: float
    population_percent_per_branch: float


class SizingParameters(BaseModel):
    power: float
    effect_size: float


class SizingDetails(BaseModel):
    metrics: dict[SizingMetricName, SizingMetric]
    parameters: SizingParameters


class SizingRecipe(BaseModel):
    app_id: str
    channel: SizingReleaseChannel
    locale: Optional[str] = None
    language: Optional[str] = None
    country: str
    new_or_existing: SizingUserType


class SizingTarget(BaseModel):
    target_recipe: SizingRecipe
    sample_sizes: dict[str, SizingDetails]


class SizingByUserType(RootModel):
    root: dict[SizingUserType, SizingTarget]


class SampleSizes(RootModel):
    root: dict[str, SizingByUserType]


class SampleSizesFactory(ModelFactory[SampleSizes]):
    __model__ = SampleSizes
