import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from mozilla_nimbus_schemas.experimenter_apis.common import (
    ExperimentBucketConfig,
    ExperimentLocalizations,
    ExperimentOutcome,
    _CommonBaseExperimentBranch,
)


class BaseExperimentV7(BaseModel):
    """The base experiment definition for V7."""

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


class NimbusExperimentV7(BaseExperimentV7):
    """A generic Nimbus experiment for V7."""

    branches: list[_CommonBaseExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )
