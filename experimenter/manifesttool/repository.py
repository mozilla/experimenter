from dataclasses import dataclass
from typing import Optional


@dataclass
class Ref:
    # The branch, tag, or bookmark name.
    name: str

    # The revision that the name resolves to, if it has been resolved.
    resolved: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        return self.resolved is not None

    def __str__(self):
        s = self.name

        if self.is_resolved:
            s = f"{s} ({self.resolved})"

        return s
