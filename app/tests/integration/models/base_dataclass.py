from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class BasePreferencesDataClass:
    preference_type: Optional[str]
    preference_branch_type: Optional[str]
    preference_value: Optional[str]
    preference_branch_name: Optional[str] = None


@dataclass(order=True)
class BaseBranchDataClass:
    branch_name: str
    preferences: List[BasePreferencesDataClass]
    addon_url: Optional[str] = None
    branch_description: Optional[str] = None
    ratio: Optional[int] = None
    ratio: Optional[int] = None


@dataclass
class BaseDataClass:
    type_name: str
    action_name: str
    experiment_type: str
    channels: str
    min_version: int
    max_version: int
    user_facing_name: str
    user_facing_description: str
    branches: List[BaseBranchDataClass]
    addon_url: str = field(default=None)
