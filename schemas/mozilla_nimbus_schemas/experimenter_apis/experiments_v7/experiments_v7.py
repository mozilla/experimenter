import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import Self

from mozilla_nimbus_schemas.experimenter_apis.common import (
    ExperimentBucketConfig,
    ExperimentLocalizations,
    ExperimentOutcome,
    _CommonDesktopExperimentBranch,
    _CommonSdkExperimentBranch,
)


class V7DesktopExperimentBranch(_CommonDesktopExperimentBranch):
    pass


class V7SdkExperimentBranch(_CommonSdkExperimentBranch):
    """The branch definition for SDK-based applications."""


class V7BaseExperiment(BaseModel):
    """The base experiment definition accessible to both Desktop and SDK experiments."""

    schemaVersion: str = Field(description="Version of the NimbusExperiment schema.")
    slug: str = Field(description="Unique identifier for the experiment.")
    id: str = Field(
        description="Unique identifier for the experiment. This is a duplicate of slug."
    )
    appName: str = Field(
        description="A slug identifying the targeted product of this experiment."
    )
    appId: str = Field(description="The platform identifier for the targeted app.")
    channel: str = Field(
        description="A specific channel of an application such as \
            'nightly', 'beta', 'release'."
    )
    userFacingName: str = Field(
        description="Public name of the experiment displayed in the UI."
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
        description="Actual enrollment end date of the experiment.", default=None
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


class V7DesktopNimbusExperiment(V7BaseExperiment):
    """A Nimbus experiment for Firefox Desktop."""

    branches: list[V7DesktopExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )

    @model_validator(mode="after")
    @classmethod
    def validate_firefox_labs(cls, data: Self) -> Self:
        if data.isRollout and data.userFacingName is None:
            raise ValueError("Firefox Labs experiments require a user-facing name.")
        return data


class V7SdkNimbusExperiment(V7BaseExperiment):
    """A Nimbus experiment for Nimbus SDK-based applications."""

    branches: list[V7SdkExperimentBranch] = Field(
        description="Branch configuration for the SDK experiment."
    )
