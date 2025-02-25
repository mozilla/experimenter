from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema
from pydantic.types import StrictInt, StrictStr
from typing_extensions import Self


class FeatureVariableType(str, Enum):
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"


class PrefBranch(str, Enum):
    DEFAULT = "default"
    USER = "user"


class DesktopApplication(str, Enum):
    FIREFOX_DESKTOP = "firefox-desktop"
    BACKGROUND_TASK = "firefox-desktop-background-task"


class SetPref(BaseModel):
    branch: PrefBranch = Field(
        description=(
            "The branch the pref will be set on.\n"
            "\n"
            "Prefs set on the user branch persists through restarts."
        ),
    )
    pref: str = Field(description="The name of the pref to set.")


class BaseFeatureVariable(BaseModel):
    description: str = Field(description="A description of the feature.")
    type: FeatureVariableType = Field(description="The field type.")


class SdkFeatureVariable(BaseFeatureVariable):
    """A feature variable."""

    enum: list[str] | SkipJsonSchema[None] = Field(
        description=(
            "An optional list of possible string values.\n"
            "\n"
            f"Only allowed when type is {FeatureVariableType.STRING.value}."
        ),
        default=None,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "dependentSchemas": {
                "enum": {
                    "properties": {
                        "type": {"const": FeatureVariableType.STRING.value},
                    }
                }
            }
        }
    )

    @model_validator(mode="after")
    @classmethod
    def validate_enum(cls, data: Self) -> Self:
        if data.enum is not None:
            if data.type != FeatureVariableType.STRING:
                raise ValueError("only string enums are supported")

            # The other cases are handled by regular model validation.

        return data


class DesktopFeatureVariable(BaseFeatureVariable):
    """A feature variable."""

    enum: list[StrictStr] | list[StrictInt] | SkipJsonSchema[None] = Field(
        description=(
            "An optional list of possible string or integer values.\n"
            "\n"
            f"Only allowed when type is {FeatureVariableType.STRING.value} or "
            f"{FeatureVariableType.INT.value}.\n"
            "\n"
            "The types in the enum must match the type of the field."
        ),
        default=None,
    )

    fallback_pref: str | SkipJsonSchema[None] = Field(
        alias="fallbackPref",
        description=(
            "A pref that provides the default value for a feature when none is present."
        ),
        default=None,
    )

    set_pref: str | SetPref | SkipJsonSchema[None] = Field(
        alias="setPref",
        description=(
            "A pref that should be set to the value of this variable when enrolling in "
            "experiments.\n"
            "\n"
            "Using a string is deprecated and unsupported in Firefox 124+."
        ),
        default=None,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "dependentSchemas": {
                # This is the equivalent of the `validate_enums` validator.
                #
                # This could also be done declaratively by specializing FeatureVariable
                # into specifically typed child classes and using a union in the parent
                # class, but that is much more verbose and generates a bunch of
                # boilerplate types.
                #
                # From a JSON Schema perspective, don't have to tuck this away in
                # dependentSchemas and the allOf clause could live at the top-level, but
                # then json-schema-to-typescript gets confused and generates an empty type
                # for `DesktopFeatureVariable`.
                "enum": {
                    "allOf": [
                        *(
                            {
                                "if": {
                                    "properties": {
                                        "type": {"const": ty},
                                    },
                                },
                                "then": {
                                    "properties": {
                                        "enum": {
                                            "items": {"type": json_schema_ty},
                                        },
                                    },
                                },
                            }
                            for ty, json_schema_ty in (
                                (FeatureVariableType.STRING, "string"),
                                (FeatureVariableType.INT, "integer"),
                            )
                        ),
                        *(
                            {
                                "if": {
                                    "properties": {
                                        "type": {"const": ty},
                                    },
                                },
                                "then": {
                                    "properties": {
                                        "enum": {"const": None},
                                    },
                                },
                            }
                            for ty in (
                                FeatureVariableType.BOOLEAN,
                                FeatureVariableType.JSON,
                            )
                        ),
                    ],
                },
                # These are the the equivalent of the
                # `validate_set_pref_fallback_pref_mutually_exclusive` validator.
                #
                # Pydantic does not have a way to encode this relationship outside custom
                # validation.
                "fallbackPref": {
                    "description": "setPref is mutually exclusive with fallbackPref",
                    "properties": {
                        "setPref": {
                            "const": None,
                        }
                    },
                },
                "setPref": {
                    "description": "fallbackPref is mutually exclusive with setPref",
                    "properties": {
                        "fallbackPref": {
                            "const": None,
                        }
                    },
                },
            },
        },
    )

    @model_validator(mode="after")
    @classmethod
    def validate_set_pref_fallback_pref_mutually_exclusive(cls, data: Self) -> Self:
        has_set_pref = data.set_pref is not None
        has_fallback_pref = data.fallback_pref is not None

        if has_set_pref and has_fallback_pref:
            raise ValueError("fallback_pref and set_pref are mutually exclusive")

        return data

    @model_validator(mode="after")
    @classmethod
    def validate_enum(cls, data: Self) -> Self:
        if data.enum is not None:
            if data.type in (FeatureVariableType.STRING, FeatureVariableType.INT):
                expected_cls = str if data.type == FeatureVariableType.STRING else int

                if not all(isinstance(variant, expected_cls) for variant in data.enum):
                    raise ValueError("enum values do not match variable type")

            # The other cases are handled by regular model validation.

        return data


class NimbusFeatureSchema(BaseModel):
    """Information about a JSON schema."""

    uri: str = Field(
        description=(
            "The resource:// or chrome:// URI that can be loaded at runtime within "
            "Firefox.\n"
            "\n"
            "Required by Firefox so that Nimbus can import the schema for validation."
        ),
    )

    path: str = Field(
        description=(
            "The path to the schema file in the source checkout.\n"
            "\n"
            "Required by Experimenter so that it can find schema files in source "
            "checkouts."
        )
    )


class BaseFeature(BaseModel):
    """The Feature type."""

    description: str = Field(description="The description of the feature.")

    has_exposure: bool = Field(
        alias="hasExposure",
        description="Whether or not this feature records exposure telemetry.",
    )

    exposure_description: str = Field(
        alias="exposureDescription",
        description=(
            "A description of the exposure telemetry collected by this feature.\n"
            "\n"
            "Only required if hasExposure is true."
        ),
        default=None,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "if": {
                "properties": {
                    "hasExposure": {
                        "const": True,
                    },
                },
            },
            "then": {
                "required": ["exposureDescription"],
            },
        }
    )

    @model_validator(mode="after")
    @classmethod
    def validate_exposure_description(cls, data: Self) -> Self:
        if data.has_exposure and data.exposure_description is None:
            raise TypeError("exposure_description is required if has_exposure is True")

        return data


class SdkFeature(BaseFeature):
    """A feature."""

    # The Nimbus SDK requires different fields for its features compared to the Desktop
    # client.

    variables: dict[str, SdkFeatureVariable] = Field(
        description="The variables that this feature can set."
    )


class DesktopFeature(BaseFeature):
    """A feature."""

    # The Firefox Desktop Nimbus client requires different fields for its features
    # compared to the SDK.

    owner: str = Field(description="The owner of the feature.")

    is_early_startup: bool = Field(
        alias="isEarlyStartup",
        description=(
            "If true, the feature values will be cached in prefs so that they can be "
            "read before Nimbus is initialized during Firefox startup."
        ),
        default=False,
    )

    applications: list[DesktopApplication] | SkipJsonSchema[None] = Field(
        description=(
            "The applications that can enroll in experiments for this feature.\n"
            "\n"
            'Defaults to "firefox-desktop".'
        ),
        default_factory=lambda: [DesktopApplication.FIREFOX_DESKTOP.value],
        min_length=1,
    )

    variables: dict[str, DesktopFeatureVariable] = Field(
        description="The variables that this feature can set.",
    )

    json_schema: NimbusFeatureSchema | SkipJsonSchema[None] = Field(
        alias="schema",
        description="An optional JSON schema that describes the feature variables.",
        default=None,
    )


class DesktopFeatureManifest(RootModel):
    """The Firefox Desktop-specific feature manifest.

    Firefox Desktop requires different fields for its features compared to the general
    Nimbus feature manifest.
    """

    root: dict[str, DesktopFeature]


class SdkFeatureManifest(RootModel):
    """The SDK-specific feature manifest."""

    root: dict[str, SdkFeature]
