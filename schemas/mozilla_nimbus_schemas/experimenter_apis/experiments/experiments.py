import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import Self

from mozilla_nimbus_schemas.experimenter_apis.common import (
    ExperimentBucketConfig,
    ExperimentFeatureConfig,
    ExperimentLocalizations,
    ExperimentOutcome,
)


class BaseExperimentBranch(BaseModel):
    slug: str = Field(description="Identifier for the branch.")
    ratio: int = Field(
        description=(
            "Relative ratio of population for the branch.\n"
            "e.g., if branch A=1 and branch B=3, then branch A \
                would get 25% of the population."
        )
    )
    features: list[ExperimentFeatureConfig] = Field(
        description="An array of feature configurations."
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


class SdkExperimentBranch(BaseExperimentBranch):
    """The branch definition for SDK-based applications.

    Supported on Firefox for Android 96+, Firefox for iOS 39+, and all versions of Cirrus.
    """


class BaseExperiment(BaseModel):
    """The base experiment definition accessible to:

    1. The Nimbus SDK via Remote Settings
    2. Jetstream via the Experimenter API
    """

    schemaVersion: str = Field(
        description="Version of the NimbusExperiment schema this experiment refers to"
    )
    slug: str = Field(description="Unique identifier for the experiment")
    id: str = Field(
        description="Unique identifier for the experiment. This is a duplicate of slug."
    )
    appName: str = Field(
        description="A slug identifying the targeted product of this experiment."
    )
    appId: str = Field(description="The platform identifier for the targeted app.")
    channel: str = Field(
        description="A specific channel of an application such as 'nightly', \
            'beta', or 'release'."
    )
    userFacingName: str = Field(
        description="Public name of the experiment displayed on 'about:studies'."
    )
    userFacingDescription: str = Field(
        description="Short public description of the experiment."
    )
    isEnrollmentPaused: bool = Field(
        description="Whether new users should be enrolled into the experiment."
    )
    isRollout: bool | SkipJsonSchema[None] = Field(
        description="Whether this experiment is a rollout.", default=None
    )
    bucketConfig: ExperimentBucketConfig = Field(description="Bucketing configuration.")
    outcomes: list[ExperimentOutcome] | SkipJsonSchema[None] = Field(
        description="List of outcomes relevant to analysis.", default=None
    )
    featureIds: list[str] | SkipJsonSchema[None] = Field(
        description="List of featureIds the experiment includes.", default=None
    )
    targeting: str | None = Field(
        description="A JEXL targeting expression.", default=None
    )
    startDate: datetime.date | None = Field(
        description="Actual publish date of the experiment."
    )
    enrollmentEndDate: datetime.date | None = Field(
        description="Actual enrollment end date.", default=None
    )
    endDate: datetime.date | None = Field(
        description="Actual end date of this experiment."
    )
    proposedDuration: int | SkipJsonSchema[None] = Field(
        description="Proposed duration of the experiment.", default=None
    )
    proposedEnrollment: int = Field(
        description="Number of days expected for new user enrollment."
    )
    referenceBranch: str | None = Field(
        description="Slug of the reference branch, if applicable."
    )
    locales: list[str] | None = Field(
        description="List of targeted locale codes.", default=None
    )
    publishedDate: datetime.datetime | None = Field(
        description="First published date to Remote Settings.", default=None
    )
    localizations: ExperimentLocalizations | None = Field(
        description="Per-locale localization substitutions.", default=None
    )

    model_config = ConfigDict(use_enum_values=True)


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
        description="Whether this experiment is a Firefox Labs Opt-In.", default=None
    )
    firefoxLabsGroup: str | None = Field(
        description="The group this should appear under in Firefox Labs", default=None
    )
    firefoxLabsTitle: str | None = Field(
        description="The title shown in Firefox Labs (Fluent ID)", default=None
    )
    firefoxLabsDescription: str | None = Field(
        description="The description shown in Firefox Labs (Fluent ID)", default=None
    )
    firefoxLabsDescriptionLinks: dict[str, HttpUrl] | None = Field(
        description="Links that will be used with the Firefox Labs \
            description Fluent ID.",
        default=None,
    )
    featureValidationOptOut: bool | SkipJsonSchema[None] = Field(
        description="Opt out of feature schema validation.", default=None
    )
    requiresRestart: bool | SkipJsonSchema[None] = Field(
        description="Does the experiment require a restart to take effect?", default=False
    )

    @model_validator(mode="after")
    @classmethod
    def validate_firefox_labs(cls, data: Self) -> Self:
        if data.isFirefoxLabsOptIn:
            if data.firefoxLabsTitle is None:
                raise ValueError(
                    "missing field firefoxLabsTitle (required for Firefox Labs)"
                )
            if data.firefoxLabsDescription is None:
                raise ValueError(
                    "missing field firefoxLabsDescription (required for Firefox Labs)"
                )
            if data.firefoxLabsGroup is None:
                raise ValueError(
                    "missing field firefoxLabsGroup (required for Firefox Labs)"
                )
            if not data.isRollout:
                for branch in data.branches:
                    if branch.firefoxLabsTitle is None:
                        raise ValueError(
                            f"branch with slug {branch.slug} is missing \
                                firefoxLabsTitle (required for Firefox Labs)"
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
