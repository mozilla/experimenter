from dataclasses import dataclass

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
    locale: str
    os: str
    os_version: str
    android_sdk_version: str | None
    debug_tag: str | None
    installation_date: int | None
    home_directory: bool | None
