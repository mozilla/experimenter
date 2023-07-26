from dataclasses import dataclass
from enum import Enum


class BaseExperimentApplications(Enum):
    FIREFOX_DESKTOP = "DESKTOP"
    FENIX = "FENIX"
    IOS = "IOS"
    FOCUS_ANDROID = "FOCUS_ANDROID"
    FOCUS_IOS = "FOCUS_IOS"


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
    min_version: int
    targeting: str | None
    percentage: float
    expected_clients: int
    locale: str | None
    countries: str | None
    languages: str | None


@dataclass
class BaseExperimentMetricsDataClass:
    primary_outcomes: list[str] | None
    secondary_outcomes: list[str] | None


@dataclass
class BaseExperimentDataClass:
    public_name: str
    hypothesis: str
    application: BaseExperimentApplications
    public_description: str
    branches: list[BaseExperimentBranchDataClass] | None
    metrics: BaseExperimentMetricsDataClass
    audience: BaseExperimentAudienceDataClass
    feature_config_id: str
    is_rollout: bool
