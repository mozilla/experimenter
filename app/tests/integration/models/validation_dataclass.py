from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field


class FilterObjectDataClass(BaseModel):
    type: Optional[str]
    channels: Optional[List]
    versions: Optional[List]


class PreferencesDataClass(BaseModel):
    preferenceBranchType: str
    preferenceType: str
    preferenceValue: Any


class BranchDataClass(BaseModel):
    slug: str
    ratio: Optional[str]
    addon_url: Optional[str] = Field(default=None)
    preferences: Optional[Dict[str, PreferencesDataClass]] = Field(default=None)


class ArgumentsDataClass(BaseModel):
    userFacingName: str
    userFacingDescription: str
    branches: List[BranchDataClass]


class APIDataClass(BaseModel):
    action_name: str
    name: str
    comment: Optional[str]
    filter_object: List[FilterObjectDataClass]
    arguments: ArgumentsDataClass
    experimenter_slug: Optional[str]
