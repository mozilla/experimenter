import re
from dataclasses import dataclass
from typing import Optional

from manifesttool.repository import Ref


@dataclass
class Version:
    """Information about a version of an app."""

    #: The major version.
    major: int

    #: The minor version.
    minor: int = 0

    #: The patch version.
    patch: int = 0

    @classmethod
    def from_match(cls, groups: dict[str, str]) -> "Version":
        """Parse a Version out of regular expression match groups.

        Args:
            groups:
                The dictionary of matches from :meth:`~re.Match.groupdict`.

        Returns:
            The parsed Version.
        """
        kwargs = {"major": int(groups["major"])}

        if minor := groups.get("minor"):
            kwargs["minor"] = int(minor)

            if patch := groups.get("patch"):
                kwargs["patch"] = int(patch)

        return cls(**kwargs)

    def as_tuple(self) -> (int, int, int):
        """Return the version as a (major, minor, patch) tuple."""
        return (self.major, self.minor, self.patch)

    def __hash__(self) -> int:
        return hash(self.as_tuple())

    def __lt__(self, other: "Version") -> bool:
        return self.as_tuple() < other.as_tuple()

    def __le__(self, other: "Version") -> bool:
        return self.as_tuple() <= other.as_tuple()

    def __gt__(self, other: "Version") -> bool:
        return self.as_tuple() > other.as_tuple()

    def __ge__(self, other: "Version") -> bool:
        return self.as_tuple() >= other.as_tuple()

    def __str__(self):  # pragma: no cover
        return f"{self.major}.{self.minor}.{self.patch}"


def find_versioned_refs(
    refs: list[Ref],
    pattern: str,
) -> dict[Version, Ref]:
    """Find all named refs that correspond to versions, according to the given
    pattern.

    Args:
        refs:
            A list of refs (e.g., branches, bookmarks, or tags).

        pattern:
            A regular expression with named capture groups for the major, minor,
            and patch components of the version.

    Returns:
        A dictionary mapping version numbers to refs.
    """
    pattern: re.Pattern = re.compile(f"^{pattern}$")

    versioned = {}
    for ref in refs:
        if m := pattern.match(ref.name):
            version = Version.from_match(m.groupdict())
            versioned[version] = ref

    return versioned


def filter_versioned_refs(
    refs: dict[Version, Ref],
    min_version: Version,
    ignore_ref_names: Optional[list[str]],
) -> dict[Version, Ref]:
    """Filter out all versions that are below the minimum version.

    Args:
        refs: A dictionary mapping Versions to Refs.
        min_version: The minimum allowed version.

    Returns:
        A new dictionary whose entries all have a version greater than or equal
        to the specified minimum verison.
    """
    return {
        v: r
        for v, r in refs.items()
        if (
            v >= min_version
            and (ignore_ref_names is None or r.name not in ignore_ref_names)
        )
    }
