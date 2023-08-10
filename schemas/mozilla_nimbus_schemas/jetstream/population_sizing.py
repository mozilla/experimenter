from enum import Enum
from typing import Type, TypedDict

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Extra


def enum_map(keys: Type[Enum], value_type: type) -> Type[TypedDict]:
    """
    This is a helper function to force the generated typescript type
    to require enum values for pydantic dicts. See
    https://github.com/phillipdupuis/pydantic-to-typescript/issues/17#issuecomment-1212341586
    for more info.
    """
    return TypedDict(
        f"Map{keys.__name__}To{value_type.__name__.title()}",
        {k.value: value_type for k in keys},
        total=False,
    )


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
    metrics: enum_map(SizingMetricName, SizingMetric)
    parameters: SizingParameters


class SizingRecipe(BaseModel):
    app_id: str
    channel: SizingReleaseChannel
    locale: str
    country: str
    new_or_existing: SizingUserType


class SizingTarget(BaseModel):
    target_recipe: SizingRecipe
    sample_sizes: dict[str, SizingDetails]


class SizingByUserType(BaseModel, extra=Extra.forbid):
    __root__: enum_map(SizingUserType, SizingTarget)


class SampleSizes(BaseModel, extra=Extra.allow):
    """
    `extra=Extra.allow` is needed for the pydantic2ts generation of
    typescript definitions. Without this, models with only a custom
    __root__ dictionary field will generate as empty types.

    See https://github.com/phillipdupuis/pydantic-to-typescript/blob/master/pydantic2ts/cli/script.py#L150-L153
    for more info.
    """

    # dynamic str key represents the concatenation of target recipe values
    __root__: dict[str, SizingByUserType]


class SampleSizesFactory(ModelFactory[SampleSizes]):
    __model__ = SampleSizes
