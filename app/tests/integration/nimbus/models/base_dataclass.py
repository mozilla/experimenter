from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class BaseExperimentApplications(Enum):
    DESKTOP = "DESKTOP"
    FENIX = "FENIX"
    IOS = "IOS"
    KLAR = "KLAR_ANDROID"
    FOCUS = "FOCUS_ANDROID"


class BaseExperimentAudienceChannels(Enum):
    UNBRANDED = ("Unbranded",)
    NIGHTLY = ("Nightly",)
    BETA = ("Beta",)
    RELEASE = "Release"


class BaseExperimentAudienceTargetingOptions(Enum):
    NO_TARGETING = ("NO_TARGETING",)
    TARGETING_FIRST_RUN = ("TARGETING_FIRST_RUN",)
    TARGETING_FIRST_RUN_CHROME_ATTRIBUTION = ("TARGETING_FIRST_RUN_CHROME_ATTRIBUTION",)
    TARGETING_FIRST_RUN_WINDOWS_1903_NEWER = ("TARGETING_FIRST_RUN_WINDOWS_1903_NEWER",)
    TARGETING_HOMEPAGE_GOOGLE = ("TARGETING_HOMEPAGE_GOOGLE",)
    TARGETING_URLBAR_FIREFOX_SUGGEST = ("TARGETING_URLBAR_FIREFOX_SUGGEST",)
    TARGETING_MAC_ONLY = ("TARGETING_MAC_ONLY",)
    TARGETING_NO_ENTERPRISE = "TARGETING_NO_ENTERPRISE"
    TARGETING_MOBILE_FIRST_RUN = "TARGETING_MOBILE_FIRST_RUN"


@dataclass
class BaseExperimentBranchDataClass:
    name: str
    description: str
    feature_config: str


@dataclass
class BaseExperimentAudienceDataClass:
    channel: BaseExperimentAudienceChannels
    min_version: int
    targeting: BaseExperimentAudienceTargetingOptions
    percentage: float
    expected_clients: int


@dataclass
class BaseExperimentMetricsDataClass:
    primary_outcomes: Optional[List[str]]
    secondary_outcomes: Optional[List[str]]


@dataclass
class BaseExperimentDataClass:
    public_name: str
    hypothesis: str
    application: BaseExperimentApplications
    public_description: str
    branches: Optional[List[BaseExperimentBranchDataClass]]
    metrics: BaseExperimentMetricsDataClass
    audience: BaseExperimentAudienceDataClass
