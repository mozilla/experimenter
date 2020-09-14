from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FilterObjectDataClass(BaseModel):
    type: Optional[str]
    channels: Optional[List]
    versions: Optional[List]


class PreferencesDataClass(BaseModel):
    preferenceBranchType: Optional[str] = None
    preferenceType: Optional[str] = None
    preferenceValue: Optional[Any] = None
    preferenceName: Optional[str] = None
    value: Optional[bool] = None


class BranchDataClass(BaseModel):
    slug: str
    ratio: Optional[str]
    preferences: Optional[Dict[Optional[str], PreferencesDataClass]] = Field(default=None)


class ArgumentsDataClass(BaseModel):
    extensionApiId: Optional[str] = None
    userFacingName: Optional[str] = None
    userFacingDescription: Optional[str] = None
    branches: Optional[List[BranchDataClass]] = None
    preferences: Optional[List[PreferencesDataClass]] = None
    slug: Optional[str] = None


class APIDataClass(BaseModel):
    name: str
    comment: Optional[str]
    filter_object: List[FilterObjectDataClass]
    experimenter_slug: Optional[str]
    action_name: Optional[str] = None
    arguments: Optional[ArgumentsDataClass] = None
