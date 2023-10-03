from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel
import yaml


class AppConfig(BaseModel):
    slug: str
    repo: str
    fml_path: str
    major_release_branch: Optional[str]
    minor_release_tag: Optional[str]


class AppConfigs(BaseModel):
    __root__: dict[str, AppConfig]

    @classmethod
    def load_from_file(cls, filename: Path) -> "AppConfigs":
        with filename.open() as f:
            app_configs: Any = yaml.safe_load(f)

        return cls.parse_obj(app_configs)
