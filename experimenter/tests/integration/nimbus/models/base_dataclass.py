from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BaseExperimentApplications(Enum):
    FIREFOX_DESKTOP = "DESKTOP"
    FIREFOX_FENIX = "FENIX"
    FIREFOX_IOS = "IOS"


class BaseExperimentAudienceChannels(Enum):
    UNBRANDED = ("Unbranded",)
    NIGHTLY = ("Nightly",)
    BETA = ("Beta",)
    RELEASE = "Release"


@dataclass
class BaseExperimentBranchDataClass:
    name: str
    description: str


@dataclass
class BaseExperimentAudienceDataClass:
    channel: BaseExperimentAudienceChannels
    min_version: str
    targeting: Optional[str]
    percentage: float
    expected_clients: int
    locale: Optional[str]
    countries: Optional[str]
    languages: Optional[str]


@dataclass
class BaseExperimentMetricsDataClass:
    primary_outcomes: Optional[list[str]]
    secondary_outcomes: Optional[list[str]]


@dataclass
class BaseExperimentDataClass:
    public_name: str
    hypothesis: str
    application: BaseExperimentApplications
    public_description: str
    branches: Optional[list[BaseExperimentBranchDataClass]]
    metrics: BaseExperimentMetricsDataClass
    audience: BaseExperimentAudienceDataClass
    feature_config_id: str
    is_rollout: bool
