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
    isRollout: Optional[bool] = None
    bucketConfig: ExperimentBucketConfig
    outcomes: Optional[List[ExperimentOutcome]] = None
    featureIds: List[str]
    branches: List[
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
    locales: Optional[List[str]] = None
