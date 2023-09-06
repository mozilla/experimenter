from typing import List, Optional, Union

from pydantic import BaseModel


class ExperimentBucketConfig(BaseModel):
    randomizationUnit: str
    namespace: str
    start: int
    count: int
    total: int


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
    features: List[ExperimentFeatureConfig]


class ExperimentMultiFeatureMobileBranch(BaseModel):
    slug: str
    ratio: int
    features: List[ExperimentFeatureConfig]


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
    outcomes: Optional[List[ExperimentOutcome]]
    featureIds: List[str]
    branches: List[
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
    locales: Optional[List[str]]
