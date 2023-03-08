from dataclasses import dataclass
from typing import List, Optional


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


@dataclass
class BaseDataClass:
    type_name: str
    experiment_type: str
    channels: str
    min_version: int
    max_version: int
    user_facing_name: Optional[str] = None
    user_facing_description: Optional[str] = None
    branches: Optional[List[BaseBranchDataClass]] = None
    action_name: Optional[str] = None
    addon_url: Optional[str] = None
