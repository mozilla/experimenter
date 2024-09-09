from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict


class RandomizationUnit(str, Enum):
    NORMANDY = "normandy_id"
    NIMBUS = "nimbus_id"
    USER_ID = "user_id"
    GROUP_ID = "group_id"


class ExperimentBucketConfig(BaseModel):
    randomizationUnit: RandomizationUnit
    namespace: str
    start: int
    count: int
    total: int

    model_config = ConfigDict(use_enum_values=True)


class ExperimentOutcome(BaseModel):
    slug: str
    priority: str


class ExperimentFeatureConfig(BaseModel):
    featureId: str
    enabled: Optional[bool] = None
    value: dict


class ExperimentSingleFeatureBranch(BaseModel):
    slug: str
    ratio: int
    feature: ExperimentFeatureConfig


class ExperimentMultiFeatureDesktopBranch(BaseModel):
    slug: str
    ratio: int
    feature: ExperimentFeatureConfig
    features: list[ExperimentFeatureConfig]


class ExperimentMultiFeatureMobileBranch(BaseModel):
    slug: str
    ratio: int
    features: list[ExperimentFeatureConfig]


class NimbusExperiment(BaseModel):
    schemaVersion: str
    slug: str
    id: str
    appName: str
    appId: str
    channel: str
    userFacingName: str
    userFacingDescription: str
    isEnrollmentPaused: bool
    isRollout: Optional[bool] = None
    bucketConfig: ExperimentBucketConfig
    outcomes: Optional[list[ExperimentOutcome]] = None
    featureIds: list[str]
    branches: list[
        Union[
            ExperimentSingleFeatureBranch,
            ExperimentMultiFeatureDesktopBranch,
            ExperimentMultiFeatureMobileBranch,
        ]
    ]
    targeting: Optional[str] = None
    startDate: Optional[str] = None
    enrollmentEndDate: Optional[str] = None
    endDate: Optional[str] = None
    proposedDuration: Optional[int] = None
    proposedEnrollment: Optional[int] = None
    referenceBranch: Optional[str] = None
    featureValidationOptOut: Optional[bool] = None
    localizations: Optional[dict] = None
    locales: Optional[list[str]] = None
