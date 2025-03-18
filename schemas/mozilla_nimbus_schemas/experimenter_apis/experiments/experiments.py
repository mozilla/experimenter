from typing import Any, Literal

from pydantic import ConfigDict, Field, HttpUrl, model_validator
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import Self

from mozilla_nimbus_schemas.experimenter_apis.common import (
    BaseExperiment,
    BaseExperimentBranch,
    ExperimentFeatureConfig,
    ExperimentLocalizations,
)


class DesktopPre95FeatureConfig(ExperimentFeatureConfig):
    featureId: Literal["this-is-included-for-desktop-pre-95-support"]
    enabled: Literal[False]
    value: dict[str, Any]


class DesktopExperimentBranch(BaseExperimentBranch):
    """The branch definition supported on Firefox Desktop 95+."""

    # Firefox Desktop-specific fields should be added to *this* schema. They will be
    # inherited by the stricter DesktopAllVersionsExperimentBranch schema.

    firefoxLabsTitle: str | None = Field(
        description="The branch title shown in Firefox Labs (Fluent ID)", default=None
    )


class SdkExperimentBranch(BaseExperimentBranch):
    """The branch definition for SDK-based applications.

    Supported on Firefox for Android 96+, Firefox for iOS 39+, and all versions of Cirrus.
    """


class DesktopAllVersionsExperimentBranch(DesktopExperimentBranch):
    """The branch definition supported on all Firefox Desktop versions.

    This version requires the feature field to be present to support older Firefox Desktop
    clients.
    """

    # Firefox Desktop-specific fields should be added to DesktopExperimentBranch. They
    # will be inherited by this schema.

    feature: DesktopPre95FeatureConfig = Field(
        description=(
            "The feature key must be provided with values to prevent crashes if the "
            "experiment is encountered by Desktop clients earlier than version 95."
        )
    )


class DesktopNimbusExperiment(BaseExperiment):
    """A Nimbus experiment for Firefox Desktop.

    This schema is less strict than DesktopAllVersionsNimbusExperiment and is intended for
    use in Firefox Desktop.
    """

    # Firefox Desktop-specific fields should be added to *this* schema. They will be
    # inherited by the stricter DesktopAllVersionsNimbusExperiment schema.

    branches: list[DesktopExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )

    isFirefoxLabsOptIn: bool = Field(
        description=(
            "When this property is set to true, treat this experiment as a"
            "Firefox Labs experiment"
        ),
        default=None,
    )
    firefoxLabsGroup: str | None = Field(
        description="The group this should appear under in Firefox Labs",
        default=None,
    )
    firefoxLabsTitle: str | None = Field(
        description="The title shown in Firefox Labs (Fluent ID)",
        default=None,
    )
    firefoxLabsDescription: str | None = Field(
        description="The description shown in Firefox Labs (Fluent ID)",
        default=None,
    )
    firefoxLabsDescriptionLinks: dict[str, HttpUrl] | None = Field(
        description=(
            "Links that will be used with the firefoxLabsDescription Fluent ID. May be "
            "null for Firefox Labs Opt-In recipes that do not use links."
        ),
        default=None,
    )
    featureValidationOptOut: bool | SkipJsonSchema[None] = Field(
        description="Opt out of feature schema validation.",
        default=None,
    )
    requiresRestart: bool | SkipJsonSchema[None] = Field(
        description=(
            "Does the experiment require a restart to take effect?\n"
            "\n"
            "Only used by Firefox Labs Opt-Ins."
        ),
        default=False,
    )
    localizations: ExperimentLocalizations | None = Field(default=None)

    @model_validator(mode="after")
    @classmethod
    def validate_firefox_labs(cls, data: Self) -> Self:
        if data.isFirefoxLabsOptIn:
            if data.firefoxLabsTitle is None:
                raise ValueError(
                    "missing field firefoxLabsTitle (required because isFirefoxLabsOptIn "
                    "is True)"
                )
            if data.firefoxLabsDescription is None:
                raise ValueError(
                    "missing field firefoxLabsDescription (required because "
                    "isFirefoxLabsOptIn is True)"
                )
            if data.firefoxLabsGroup is None:
                raise ValueError(
                    "missing field firefoxLabsGroup (required because isFirefoxLabsOptIn "
                    "is True)"
                )
            if not data.isRollout:
                for branch in data.branches:
                    if branch.firefoxLabsTitle is None:
                        raise ValueError(
                            f"branch with slug {branch.slug} is missing "
                            "firefoxLabsTitle field "
                            "(required because firefoxLabsTitle is True)"
                        )

        return data

    model_config = ConfigDict(
        json_schema_extra={
            "dependentSchemas": {
                "isFirefoxLabsOptIn": {
                    "if": {
                        "properties": {
                            "isFirefoxLabsOptIn": {"const": True},
                        },
                    },
                    "then": {
                        "required": [
                            "firefoxLabsDescription",
                            "firefoxLabsDescriptionLinks",
                            "firefoxLabsGroup",
                            "firefoxLabsTitle",
                        ],
                        "if": {
                            "properties": {
                                "isRollout": {"const": False},
                            },
                            "required": ["isRollout"],
                        },
                        "then": {
                            "properties": {
                                "branches": {
                                    "items": {
                                        "required": ["firefoxLabsTitle"],
                                    },
                                },
                            },
                        },
                    },
                }
            }
        }
    )


class DesktopAllVersionsNimbusExperiment(DesktopNimbusExperiment):
    """A Nimbus experiment for Firefox Desktop.

    This schema is more strict than DesktopNimbusExperiment and is backwards
    comaptible with Firefox Desktop versions less than 95. It is intended for use inside
    Experimenter itself.
    """

    # Firefox Desktop-specific fields should be added to DesktopNimbusExperiment. They
    # will be inherited by this schema.

    branches: list[DesktopAllVersionsExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )


class SdkNimbusExperiment(BaseExperiment):
    """A Nimbus experiment for Nimbus SDK-based applications."""

    branches: list[SdkExperimentBranch] = Field(
        description="Branch configuration for the SDK experiment."
    )
