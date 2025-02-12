# experimenter_apis/common.py

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class RandomizationUnit(str, Enum):
    """A unique, stable identifier for the user used as an input to bucket hashing."""

    NORMANDY = "normandy_id"
    NIMBUS = "nimbus_id"
    USER_ID = "user_id"
    GROUP_ID = "group_id"


class ExperimentBucketConfig(BaseModel):
    """Common Bucketing Configuration used across all versions."""

    # NB: We can't include a description on the randomizationUnit field because that
    # causes json-schema-to-typescript to generate an extra RandomizationUnit1 type. See
    # https://github.com/bcherny/json-schema-to-typescript/issues/466

    randomizationUnit: RandomizationUnit
    namespace: str = Field(description="Additional inputs to the hashing function.")
    start: int = Field(description="Index of the starting bucket of the range.")
    count: int = Field(description="Number of buckets in the range.")
    total: int = Field(
        description="The total number of buckets. You can assume \
            this will always be 10000."
    )

    model_config = ConfigDict(use_enum_values=True)


class ExperimentOutcome(BaseModel):
    slug: str = Field(description="Identifier for the outcome.")
    priority: str = Field(description='e.g., "primary" or "secondary".')


class ExperimentFeatureConfig(BaseModel):
    featureId: str = Field(description="The identifier for the feature flag.")
    value: dict[str, Any] = Field(
        description="The values that define the feature configuration."
    )


class ExperimentLocalizations(RootModel[dict[str, dict[str, str]]]):
    """Per-locale localization substitutions.

    The top level key is the locale (e.g., "en-US" or "fr"). Each entry is a mapping of
    string IDs to their localized equivalents.
    """

    model_config = ConfigDict(title="ExperimentLocalizations")


class _CommonBaseExperimentBranch(BaseModel):
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


class _CommonDesktopExperimentBranch(_CommonBaseExperimentBranch):
    """The branch definition supported on Firefox Desktop 95+."""

    # Firefox Desktop-specific fields should be added to *this* schema. They will be
    # inherited by the stricter DesktopAllVersionsExperimentBranch schema.

    firefoxLabsTitle: str | None = Field(
        description="The branch title shown in Firefox Labs (Fluent ID)", default=None
    )


class _CommonSdkExperimentBranch(_CommonBaseExperimentBranch):
    """The branch definition for SDK-based applications.

    Supported on Firefox for Android 96+, Firefox for iOS 39+, and all versions of Cirrus.
    """
