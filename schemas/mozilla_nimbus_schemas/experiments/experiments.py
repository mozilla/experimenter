from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel


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

    class Config:
        use_enum_values = True


class ExperimentOutcome(BaseModel):
    slug: str
    priority: str


class ExperimentFeatureConfig(BaseModel):
    featureId: str
    enabled: Optional[bool]
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
    isRollout: Optional[bool]
    bucketConfig: ExperimentBucketConfig
    outcomes: Optional[list[ExperimentOutcome]]
    featureIds: list[str]
    branches: list[
        Union[
            ExperimentSingleFeatureBranch,
            ExperimentMultiFeatureDesktopBranch,
            ExperimentMultiFeatureMobileBranch,
        ]
    ]
    targeting: Optional[str]
    startDate: Optional[str]
    enrollmentEndDate: Optional[str]
    endDate: Optional[str]
    proposedDuration: Optional[int]
    proposedEnrollment: Optional[int]
    referenceBranch: Optional[str]
    featureValidationOptOut: Optional[bool]
    localizations: Optional[dict]
    locales: Optional[list[str]]
