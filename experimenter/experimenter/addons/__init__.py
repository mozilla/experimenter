import json
from datetime import datetime

from django.conf import settings
from django.core.checks import Error, register
from pydantic import BaseModel, RootModel

NEWTAB_ADDON = "newtab"
VERSIONS_FILENAME = "versions.json"


class AddonVersion(BaseModel):
    version: str
    shipit_release: str
    xpi_revision: str
    created: datetime

    @property
    def sort_key(self) -> tuple[int, ...]:
        return tuple(int(part) for part in self.version.split("."))


class AddonVersions(RootModel[list[AddonVersion]]):
    pass


class Addons:
    _versions: dict[str, list[AddonVersion]] | None = None

    @classmethod
    def _load_versions(cls) -> dict[str, list[AddonVersion]]:
        versions: dict[str, list[AddonVersion]] = {}

        for addon_path in settings.ADDON_VERSIONS_PATH.iterdir():
            if not addon_path.is_dir():
                continue

            with (addon_path / VERSIONS_FILENAME).open() as versions_file:
                versions[addon_path.name] = AddonVersions.model_validate(
                    json.load(versions_file)
                ).root

        return versions

    @classmethod
    def clear_cache(cls):
        cls._versions = None

    @classmethod
    def all(cls) -> dict[str, list[AddonVersion]]:
        if cls._versions is None:
            cls._versions = cls._load_versions()

        return cls._versions

    @classmethod
    def by_addon(cls, addon: str) -> list[AddonVersion]:
        return cls.all().get(addon, [])


@register()
def check_addon_versions(app_configs, **kwargs):
    errors = []

    try:
        Addons.all()
    except Exception as e:
        errors.append(Error(f"Error loading Addon Versions: {e}"))
    return errors
