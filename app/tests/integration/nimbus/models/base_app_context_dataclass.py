from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass(frozen=True)
class BaseAppContextDataClass:
    app_id: str
    app_name: str
    channel: str
    app_version: str
    app_build: str
    architecture: str
    device_manufacturer: str
    device_model: str
    language: str
    os: str
    os_version: str
    android_sdk_version: Optional[str]
    debug_tag: Optional[str]
    installation_date: Optional[int]
    home_directory: Optional[bool]
    custom_targeting_attributes: Optional[dict]
