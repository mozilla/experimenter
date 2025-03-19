import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel
from pydantic.json_schema import SkipJsonSchema


class RandomizationUnit(str, Enum):
    """A unique, stable identifier for the user used as an input to bucket hashing."""

    NORMANDY = "normandy_id"
    NIMBUS = "nimbus_id"
    USER_ID = "user_id"
    GROUP_ID = "group_id"


class ExperimentBucketConfig(BaseModel):
    # NB: We can't include a description on the randomizationUnit field because that
    # causes json-schema-to-typescript to generate an extra RandomizationUnit1 type. See
    # https://github.com/bcherny/json-schema-to-typescript/issues/466

    randomizationUnit: RandomizationUnit
    namespace: str = Field(description="Additional inputs to the hashing function.")
    start: int = Field(description="Index of the starting bucket of the range.")
    count: int = Field(description="Number of buckets in the range.")
    total: int = Field(
        description=(
            "The total number of buckets.\n"
            "\n"
            "You can assume this will always be 10000."
        )
    )

    model_config = ConfigDict(use_enum_values=True)


class ExperimentOutcome(BaseModel):
    slug: str = Field(description="Identifier for the outcome.")
    priority: str = Field(description='e.g., "primary" or "secondary".')


class ExperimentFeatureConfig(BaseModel):
    featureId: str = Field(description="The identifier for the feature flag.")
    value: dict[str, Any] = Field(
        description=(
            "The values that define the feature configuration.\n"
            "\n"
            "This should be validated against a schema."
        )
    )


class ExperimentLocalizations(RootModel[dict[str, dict[str, str]]]):
    """Per-locale localization substitutions.

    The top level key is the locale (e.g., "en-US" or "fr"). Each entry is a mapping of
    string IDs to their localized equivalents.
    """

    model_config = ConfigDict(title="ExperimentLocalizations")


class BaseExperimentBranch(BaseModel):
    slug: str = Field(description="Identifier for the branch.")
    ratio: int = Field(
        description=(
            "Relative ratio of population for the branch.\n"
            "\n"
            "e.g., if branch A=1 and branch B=3, then branch A would get 25% of the "
            "population."
        )
    )
    features: list[ExperimentFeatureConfig] = Field(
        description="An array of feature configurations."
    )


class BaseExperiment(BaseModel):
    """Common base class that contains all fields included in both the v6 and v7 "
    Experiment API.
    """

    schemaVersion: str = Field(
        description="Version of the NimbusExperiment schema this experiment refers to"
    )
    slug: str = Field(description="Unique identifier for the experiment")
    id: str = Field(
        description=(
            "Unique identifier for the experiiment.\n"
            "\n"
            "This is a duplicate of slug, but is required field for all Remote Settings "
            "records."
        )
    )
    appName: str = Field(
        description=(
            "A slug identifying the targeted product of this experiment.\n"
            "\n"
            "It should be a lowercased_with_underscores name that is short and "
            "unambiguous and it should match the app_name found in "
            "https://probeinfo.telemetry.mozilla.org/glean/repositories. Examples are "
            '"fenix" and "firefox_desktop".'
        )
    )
    appId: str = Field(
        description=(
            "The platform identifier for the targeted app.\n"
            "\n"
            "This should match app's identifier exactly as it appears in the relevant "
            "app store listing (for relevant platforms) or the app's Glean "
            "initialization (for other platforms).\n"
            "\n"
            'Examples are "org.mozilla.firefox_beta" and "firefox-desktop".'
        )
    )
    channel: str = Field(
        description=(
            'A specific channel of an application such as "nightly", "beta", or '
            '"release".'
        )
    )
    userFacingName: str = Field(
        description=(
            'Public name of the experiment that will be displayed on "about:studies".'
        )
    )
    userFacingDescription: str = Field(
        description=(
            "Short public description of the experiment that will be displayed on "
            '"about:studies".'
        )
    )
    isEnrollmentPaused: bool = Field(
        description=(
            "When this property is set to true, the SDK should not enroll new users "
            "into the experiment that have not already been enrolled."
        )
    )
    isRollout: bool | SkipJsonSchema[None] = Field(
        description=(
            "When this property is set to true, treat this experiment as a rollout.\n"
            "\n"
            "Rollouts are currently handled as single-branch experiments separated from "
            "the bucketing namespace for normal experiments.\n"
            "\n"
            "See-also: https://mozilla-hub.atlassian.net/browse/SDK-405"
        ),
        default=None,
    )
    bucketConfig: ExperimentBucketConfig = Field(description="Bucketing configuration.")
    outcomes: list[ExperimentOutcome] | SkipJsonSchema[None] = Field(
        description="A list of outcomes relevant to the experiment analysis.",
        default=None,
    )
    featureIds: list[str] = Field(
        description="A list of featureIds the experiment contains configurations for.",
    )
    targeting: str | None = Field(
        description="A JEXL targeting expression used to filter out experiments.",
        default=None,
    )
    startDate: datetime.date | None = Field(
        description=(
            "Actual publish date of the experiment.\n"
            "\n"
            "Note that this value is expected to be null in Remote Settings."
        ),
    )
    enrollmentEndDate: datetime.date | None = Field(
        description=(
            "Actual enrollment end date of the experiment.\n"
            "\n"
            "Note that this value is expected to be null in Remote Settings."
        ),
        default=None,
    )
    endDate: datetime.date | None = Field(
        description=(
            "Actual end date of this experiment.\n"
            "\n"
            "Note that this field is expected to be null in Remote Settings."
        ),
    )
    proposedDuration: int | SkipJsonSchema[None] = Field(
        description=(
            "Duration of the experiment from the start date in days.\n"
            "\n"
            "Note that this property is only used during the analysis phase (i.e., not "
            "by the SDK)."
        ),
        default=None,
    )
    proposedEnrollment: int = Field(
        description=(
            "This represents the number of days that we expect to enroll new users.\n"
            "\n"
            "Note that this property is only used during the analysis phase (i.e., not "
            "by the SDK)."
        )
    )
    referenceBranch: str | None = Field(
        description=(
            'The slug of the reference branch (i.e., the branch we consider "control").'
        )
    )
    locales: list[str] | None = Field(
        description=(
            'The list of locale codes (e.g., "en-US" or "fr") that this experiment is '
            "targeting.\n"
            "\n"
            "If null, all locales are targeted."
        ),
        default=None,
    )
    localizations: ExperimentLocalizations | None = Field(
        description="Per-locale localization substitutions.", default=None
    )
    publishedDate: datetime.datetime | None = Field(
        description=(
            "The date that this experiment was first published to Remote Settings.\n"
            "\n"
            "If null, it has not yet been published."
        ),
        default=None,
    )

    model_config = ConfigDict(use_enum_values=True)
