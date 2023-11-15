from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, root_validator


class RepositoryType(Enum):
    HGMO = "hgmo"  # hg.mozilla.org
    GITHUB = "github"


class Repository(BaseModel):
    type: RepositoryType
    name: str


class VersionFileType(str, Enum):
    PLAIN_TEXT = "plaintext"
    PLIST = "plist"


class PlainTextVersionFile(BaseModel):
    type: Literal[VersionFileType.PLAIN_TEXT]
    path: str


class PListVersionFile(BaseModel):
    type: Literal[VersionFileType.PLIST]
    path: str
    key: str


class VersionFile(BaseModel):
    __root__: Union[PlainTextVersionFile, PListVersionFile] = Field(discriminator="type")


class AppConfig(BaseModel):
    """The configuration of a single app in apps.yaml."""

    slug: str
    repo: Repository
    fml_path: Optional[str]
    experimenter_yaml_path: Optional[str]
    branch_re: Optional[str]
    tag_re: Optional[str]
    ignored_branches: Optional[list[str]]
    ignored_tags: Optional[list[str]]
    version_file: Optional[VersionFile]

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
    def load_from_directory(cls, directory: Path) -> "AppConfigs":
        """Load the app configurations and parse them."""
        filename = directory / "apps.yaml"

        with filename.open() as f:
            app_configs: Any = yaml.safe_load(f)

        return cls.parse_obj(app_configs)
