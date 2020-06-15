from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict


@dataclass
class BasePreferencesClass:
    preference_type: Optional[str]
    preference_branch_type: Optional[str]
    preference_value: Optional[str]
    preference_branch_name: str = field(default=None)


@dataclass
class BaseBranchData:
    branch_name: str
    preferences: BasePreferencesClass
    addon_url: str = field(default=None)
    branch_description: str = field(default=None)
    ratio: Optional[int] = field(default=None)


@dataclass
class BaseJsonData:
    type_name: str
    action_name: str
    experiment_type: str
    channels: str
    min_version: int
    max_version: int
    user_facing_name: str
    user_facing_description: str
    branches: BaseBranchData
    addon_url: str = field(default=None)
