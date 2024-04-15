from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, root_validator

from manifesttool.version import Version


class RepositoryType(str, Enum):
    HGMO = "hgmo"  # hg.mozilla.org
    GITHUB = "github"


class Repository(BaseModel):
    type: RepositoryType
    name: str
    default_branch: str = Field(default="main")

    @root_validator(pre=True)
    def validate_default_branch(cls, values):
        ty = values.get("type")
        default_branch = values.get("default_branch")

        if ty == RepositoryType.HGMO and default_branch is None:
            raise ValueError("hg.mozilla.org-hosted repositories require default_branch")

        return values


class VersionFileType(str, Enum):
    PLAIN_TEXT = "plaintext"
    PLIST = "plist"


class PlainTextVersionFile(BaseModel):
    type: Literal[VersionFileType.PLAIN_TEXT]
    path: Optional[Union[str, list[str]]]


class PListVersionFile(BaseModel):
    type: Literal[VersionFileType.PLIST]
    path: Optional[Union[str, list[str]]]
    key: str


class VersionFile(BaseModel):
    __root__: Union[PlainTextVersionFile, PListVersionFile] = Field(discriminator="type")

    @classmethod
    def create_plain_text(cls, path: str | list[str]):  # pragma: no cover
        return cls(
            __root__=PlainTextVersionFile(
                type=VersionFileType.PLAIN_TEXT,
                path=path,
            ),
        )

    @classmethod
    def create_plist(cls, path: str | list[str], key: str):  # pragma: no cover
        return cls(
            __root__=PListVersionFile(
                type=VersionFileType.PLIST,
                path=path,
                key=key,
            ),
        )


class DiscoveryStrategyType(str, Enum):
    TAGGED = "tagged"
    BRANCHED = "branched"


class TaggedDiscoveryStrategy(BaseModel):
    type: Literal[DiscoveryStrategyType.TAGGED]
    branch_re: str
    tag_re: Optional[str]
    ignored_branches: Optional[list[str]]
    ignored_tags: Optional[list[str]]
    ignored_versions: Optional[list[Version]]


class BranchedDiscoveryStrategy(BaseModel):
    type: Literal[DiscoveryStrategyType.BRANCHED]
    branches: Optional[list[str]]


class DiscoveryStrategy(BaseModel):
    __root__: Union[TaggedDiscoveryStrategy, BranchedDiscoveryStrategy] = Field(
        discriminator="type"
    )

    @classmethod
    def create_tagged(
        cls,
        *,
        branch_re: Optional[str],
        tag_re: Optional[str] = None,
        ignored_branches: Optional[list[str]] = None,
        ignored_tags: Optional[list[str]] = None,
        ignored_versions: Optional[list[Version]] = None,
    ):  # pragma: no cover
        return cls(
            __root__=TaggedDiscoveryStrategy(
                type=DiscoveryStrategyType.TAGGED,
                branch_re=branch_re,
                tag_re=tag_re,
                ignored_branches=ignored_branches,
                ignored_tags=ignored_tags,
                ignored_versions=ignored_versions,
            )
        )

    @classmethod
    def create_branched(cls, branches: Optional[list[str]] = None):  # pragma: no cover
        return cls(
            __root__=BranchedDiscoveryStrategy(
                type=DiscoveryStrategyType.BRANCHED,
                branches=branches,
            ),
        )


class ReleaseDiscovery(BaseModel):
    version_file: VersionFile
    strategies: list[DiscoveryStrategy] = Field(min_items=1)


class AppConfig(BaseModel):
    """The configuration of a single app in apps.yaml."""

    slug: str
    repo: Repository
    fml_path: Optional[Union[str, list[str]]]
    experimenter_yaml_path: Optional[str]
    release_discovery: Optional[ReleaseDiscovery]

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
