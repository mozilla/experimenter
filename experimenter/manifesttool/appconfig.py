from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, root_validator


class RepositoryType(Enum):
    HGMO = "hgmo"  # hg.mozilla.org
    GITHUB = "github"


class Repository(BaseModel):
    type: RepositoryType
    name: str


class AppConfig(BaseModel):
    """The configuration of a single app in apps.yaml."""

    slug: str
    repo: Repository
    fml_path: Optional[str]
    experimenter_yaml_path: Optional[str]
    major_release_branch: Optional[str]
    minor_release_tag: Optional[str]

    @root_validator(pre=True)
    def validate_one_manifest_path(cls, values):
        has_fml_path = values.get("fml_path") is not None
        has_legacy_path = values.get("experimenter_yaml_path") is not None

        if not has_fml_path and not has_legacy_path:
            raise ValueError("one of fml_path and experimenter_yaml_path is required")

        if has_fml_path and has_legacy_path:
            raise ValueError("fml_path and experimenter_yaml_path are mutually exclusive")

        return values


class AppConfigs(BaseModel):
    """The entire apps.yaml model as a pydantic model."""

    __root__: dict[str, AppConfig]

    @classmethod
    def load_from_file(cls, filename: Path) -> "AppConfigs":
        """Load the app configurations and parse them."""
        with filename.open() as f:
            app_configs: Any = yaml.safe_load(f)

        return cls.parse_obj(app_configs)
