from enum import Enum

from pydantic import BaseModel


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
    locale: str
    country: str
    new_or_existing: SizingUserType
    minimum_version: str


class SizingTarget(BaseModel):
    target_recipe: SizingRecipe
    sample_sizes: dict[str, SizingDetails]


class SizingByUserType(BaseModel):
    __root__: dict[SizingUserType, SizingTarget]


class SampleSizes(BaseModel):
    # dynamic key representing the target for easy lookup
    __root__: dict[str, SizingByUserType]
