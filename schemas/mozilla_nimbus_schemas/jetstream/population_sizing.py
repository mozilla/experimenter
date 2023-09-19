from enum import Enum
from typing import Optional

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Extra


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
    locale: Optional[str] = None
    language: Optional[str] = None
    country: str
    new_or_existing: SizingUserType


class SizingTarget(BaseModel):
    target_recipe: SizingRecipe
    sample_sizes: dict[str, SizingDetails]


class SizingByUserType(BaseModel, extra=Extra.allow):
    """
    `extra=Extra.allow` is needed for the pydantic2ts generation of
    typescript definitions. Without this, models with only a custom
    __root__ dictionary field will generate as empty types.

    See https://github.com/phillipdupuis/pydantic-to-typescript/blob/master/pydantic2ts/cli/script.py#L150-L153
    and https://github.com/phillipdupuis/pydantic-to-typescript/issues/39
    for more info.

    If this is fixed we should remove `extra=Extra.allow`.
    """

    __root__: dict[SizingUserType, SizingTarget]


class SampleSizes(BaseModel, extra=Extra.allow):
    """
    `extra=Extra.allow` is needed for the pydantic2ts generation of
    typescript definitions. Without this, models with only a custom
    __root__ dictionary field will generate as empty types.

    See https://github.com/phillipdupuis/pydantic-to-typescript/blob/master/pydantic2ts/cli/script.py#L150-L153
    and https://github.com/phillipdupuis/pydantic-to-typescript/issues/39
    for more info.

    If this is fixed we should remove `extra=Extra.allow`.
    """

    # dynamic str key represents the concatenation of target recipe values
    __root__: dict[str, SizingByUserType]


class SampleSizesFactory(ModelFactory[SampleSizes]):
    __model__ = SampleSizes
