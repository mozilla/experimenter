from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BaseBranchDataClass:
    name: str
    description: str
    config: str


@dataclass
class BaseAudienceDataClass:
    channel: str
    min_version: int
    targeting: str
    percentage: float
    expected_clients: int


@dataclass
class BaseDataClass:
    hypothesis: str
    application: str
    public_description: str
    branches: Optional[List[BaseBranchDataClass]]
    audience: BaseAudienceDataClass
    public_name: Optional[str] = None
