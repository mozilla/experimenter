from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Extra, Field


class FeatureVariableType(Enum):
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"


class PrefBranch(Enum):
    DEFAULT = "default"
    USER = "user"


class SetPref(BaseModel):
    branch: PrefBranch
    pref: str


class FeatureVariable(BaseModel):
    description: Optional[str]
    enum: Optional[list[str]]
    fallback_pref: Optional[str] = Field(alias="fallbackPref")
    type: Optional[FeatureVariableType]
    set_pref: Optional[Union[str, SetPref]] = Field(alias="setPref")


class NimbusFeatureSchema(BaseModel):
    uri: str
    path: str


class BaseFeature(BaseModel):
    """The base Feature type.

    The real Feature type has conditionally required fields (if the feature has
    exposure, then the exposure description is required), so this class includes
    the fields common in both cases.
    """

    description: Optional[str]
    is_early_startup: Optional[bool] = Field(alias="isEarlyStartup")
    variables: dict[str, FeatureVariable]

    #: Only used by Firefox Desktop.
    json_schema: Optional[NimbusFeatureSchema] = Field(alias="schema")


class FeatureWithExposure(BaseFeature):
    """A feature that has exposure."""

    has_exposure: Literal[True] = Field(alias="hasExposure")
    exposure_description: str = Field(alias="exposureDescription")


class FeatureWithoutExposure(BaseFeature):
    """A feature without exposure."""

    has_exposure: Literal[False] = Field(alias="hasExposure")

    @property
    def exposure_description(self):
        return None


class Feature(BaseModel):
    __root__: Union[FeatureWithExposure, FeatureWithoutExposure] = Field(
        discriminator="has_exposure"
    )


# `extra=Extra.allow` is needed for the pydantic2ts generation of
# typescript definitions. Without this, models with only a custom
# __root__ dictionary field will generate as empty types.
#
# See https://github.com/phillipdupuis/pydantic-to-typescript/blob/master/pydantic2ts/cli/script.py#L150-L153
# and https://github.com/phillipdupuis/pydantic-to-typescript/issues/39
# for more info.
#
# If this is fixed we should remove `extra=Extra.allow`.
class FeatureManifest(BaseModel, extra=Extra.allow):
    __root__: dict[str, Feature]
