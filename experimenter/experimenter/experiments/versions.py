from typing import Annotated

import packaging.version
import yaml
from django.conf import settings
from django.core.checks import Error, register
from django.db import models
from pydantic import RootModel, StringConstraints, model_validator

FIREFOX_VERSION_NAME_PATTERN = r"^FIREFOX_[0-9A-Z_]+$"
FIREFOX_VERSION_VALUE_PATTERN = r"^\d+\.(!|\d+\.\d+|0b\d+)$"

FirefoxVersionName = Annotated[
    str, StringConstraints(pattern=FIREFOX_VERSION_NAME_PATTERN, strict=True)
]
FirefoxVersionValue = Annotated[
    str, StringConstraints(pattern=FIREFOX_VERSION_VALUE_PATTERN, strict=True)
]


class FirefoxVersions(RootModel[dict[FirefoxVersionName, FirefoxVersionValue]]):
    @model_validator(mode="after")
    def check_unique_values(self):
        values = list(self.root.values())

        if len(values) != len(set(values)):
            raise ValueError("Duplicate Firefox version values")

        return self


class VersionsLoader:
    _versions = None

    @classmethod
    def _load_versions(cls):
        with settings.FIREFOX_VERSIONS_PATH.open() as versions_file:
            return FirefoxVersions.model_validate(yaml.safe_load(versions_file)).root

    @classmethod
    def clear_cache(cls):
        cls._versions = None

    @classmethod
    def all(cls):
        if cls._versions is None:
            cls._versions = cls._load_versions()

        return cls._versions


@register()
def check_firefox_versions(app_configs, **kwargs):
    errors = []

    try:
        VersionsLoader.all()
    except Exception as e:
        errors.append(Error(f"Error loading Firefox Versions: {e}"))

    return errors


class VersionChoices(models.TextChoices):
    @staticmethod
    def parse(version_str: str) -> packaging.version.Version:
        return packaging.version.parse(version_str.replace("!", "0"))


Version = VersionChoices(
    "Version",
    [("NO_VERSION", ""), *VersionsLoader.all().items()],
)
