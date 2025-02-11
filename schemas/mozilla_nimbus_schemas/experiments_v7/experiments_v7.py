import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import Self


class V7RandomizationUnit(str, Enum):
    """A unique, stable identifier for the user used as an input to bucket hashing."""

    NORMANDY = "normandy_id"
    NIMBUS = "nimbus_id"
    USER_ID = "user_id"
    GROUP_ID = "group_id"


class V7ExperimentBucketConfig(BaseModel):
    randomizationUnit: V7RandomizationUnit
    namespace: str = Field(description="Additional inputs to the hashing function.")
    start: int = Field(description="Index of the starting bucket of the range.")
    count: int = Field(description="Number of buckets in the range.")
    total: int = Field(
        description="The total number of buckets. You can assume this will \
            always be 10000."
    )

    model_config = ConfigDict(use_enum_values=True)


class V7ExperimentOutcome(BaseModel):
    slug: str = Field(description="Identifier for the outcome.")
    priority: str = Field(description='e.g., "primary" or "secondary".')


class V7ExperimentFeatureConfig(BaseModel):
    featureId: str = Field(description="The identifier for the feature flag.")
    value: dict[str, Any] = Field(
        description="The values that define the feature configuration."
    )


class V7BaseExperimentBranch(BaseModel):
    slug: str = Field(description="Identifier for the branch.")
    ratio: int = Field(description="Relative ratio of population for the branch.")
    features: list[V7ExperimentFeatureConfig] = Field(
        description="An array of feature configurations."
    )


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
        description="A specific channel of an application such as 'nightly', \
            'beta', 'release'."
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
    bucketConfig: V7ExperimentBucketConfig = Field(description="Bucketing configuration.")
    outcomes: list[V7ExperimentOutcome] | SkipJsonSchema[None] = Field(
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

    model_config = ConfigDict(use_enum_values=True)


class V7DesktopExperimentBranch(V7BaseExperimentBranch):
    firefoxLabsTitle: str | None = Field(
        description="The branch title shown in Firefox Labs.", default=None
    )


class V7SdkExperimentBranch(V7BaseExperimentBranch):
    """The branch definition for SDK-based applications."""


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
