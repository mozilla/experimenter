from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, RootModel


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
    description: Optional[str] = None
    enum: Optional[list[str]] = None
    fallback_pref: Optional[str] = Field(None, alias="fallbackPref")
    type: Optional[FeatureVariableType] = None
    set_pref: Optional[Union[str, SetPref]] = Field(None, alias="setPref")


class NimbusFeatureSchema(BaseModel):
    uri: str
    path: str


class BaseFeature(BaseModel):
    """The base Feature type.

    The real Feature type has conditionally required fields (if the feature has
    exposure, then the exposure description is required), so this class includes
    the fields common in both cases.
    """

    description: Optional[str] = None
    is_early_startup: Optional[bool] = Field(None, alias="isEarlyStartup")
    variables: dict[str, FeatureVariable]

    #: Only used by Firefox Desktop.
    json_schema: Optional[NimbusFeatureSchema] = Field(None, alias="schema")


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


class Feature(RootModel):
    root: Union[FeatureWithExposure, FeatureWithoutExposure] = Field(
        discriminator="has_exposure"
    )


class FeatureManifest(RootModel):
    root: dict[str, Feature]
