from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
import yaml


@dataclass
class Ref:
    # The branch, tag, or bookmark name.
    name: str

    # The revision that the name resolves to, if it has been resolved.
    target: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        return self.target is not None

    def __str__(self):
        s = self.name

        if self.is_resolved:
            s = f"{s} ({self.target})"

        return s


class RefCache(BaseModel):
    __root__: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def load_or_create(cls, path: Path) -> "RefCache":
        try:
            return cls.load_from_file(path)
        except FileNotFoundError:
            return RefCache()

    @classmethod
    def load_from_file(cls, path: Path) -> "RefCache":
        with path.open("r") as f:
            cache = yaml.safe_load(f)

        return cls.parse_obj(cache)

    def write_to_file(self, path: Path):
        with path.open("w") as f:
            yaml.safe_dump(self.__root__, f)

    def get(self, name: str) -> Optional[Ref]:
        if target := self.__root__.get(name):
            return Ref(name, target)

        return None

    def add(self, ref: Ref):
        assert ref.is_resolved
        self.__root__[ref.name] = ref.target
