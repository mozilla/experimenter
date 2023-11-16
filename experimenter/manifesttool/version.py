import plistlib
import re
from dataclasses import dataclass
from typing import Iterable, Optional

from manifesttool import github_api, hgmo_api
from manifesttool.appconfig import AppConfig, RepositoryType, VersionFile, VersionFileType
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

    VERSION_RE = re.compile(r"^(?P<major>\d+)(?:\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?)?")

    @classmethod
    def parse(cls, s: str) -> Optional["Version"]:
        """Parse a version out of a given string.

        Any missing component will be assumed zero.

        Trailing signifiers (e.g., b0, a0, rc1) will be ignored.
        """
        if m := cls.VERSION_RE.match(s):
            return cls.from_match(m.groupdict())

        return None

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
    ignored_ref_names: Optional[list[str]],
) -> dict[Version, Ref]:
    """Find all named refs that correspond to versions, according to the given
    pattern.

    Args:
        refs:
            A list of refs (e.g., branches, bookmarks, or tags).

        pattern:
            A regular expression with named capture groups for the major, minor,
            and patch components of the version.

        ignored_ref_names:
            An list of refs that should be ignored.

    Returns:
        A dictionary mapping version numbers to refs.
    """
    pattern: re.Pattern = re.compile(f"^{pattern}$")

    versioned = {}
    for ref in refs:
        if ignored_ref_names and ref.name in ignored_ref_names:
            continue

        if m := pattern.match(ref.name):
            version = Version.from_match(m.groupdict())
            versioned[version] = ref

    return versioned


def filter_versioned_refs(
    refs: dict[Version, Ref],
    min_version: Version,
) -> dict[Version, Ref]:
    """Filter out all versions that are below the minimum version.

    Args:
        refs: A dictionary mapping Versions to Refs.
        min_version: The minimum allowed version.

    Returns:
        A new dictionary whose entries all have a version greater than or equal
        to the specified minimum verison.
    """
    return {v: r for v, r in refs.items() if v >= min_version}


def parse_version_file(f: VersionFile, contents: str) -> Optional[Version]:
    """Parse a version file and return the version.

    Args:
        f: The ``VersionFile`` definition.
        contents: The contents of the file.

    Returns:
        The parsed Version.
    """
    if f.__root__.type == VersionFileType.PLAIN_TEXT:
        return _parse_plain_text_version_file(contents)
    elif f.__root__.type == VersionFileType.PLIST:
        return _parse_plist_version_file(contents, f.__root__.key)


def _parse_plain_text_version_file(contents: str) -> Optional[Version]:
    return Version.parse(contents)


def _parse_plist_version_file(contents: str, key: str) -> Optional[Version]:
    plist = plistlib.loads(contents.encode())
    version_str = plist[key]

    return Version.parse(version_str)


def resolve_ref_versions(
    app_config: AppConfig,
    refs: Iterable[Ref],
) -> dict[Version, Ref]:
    """Resolve refs to versions based on the contents of their version file.

    Args:
        app_config: The AppConfig for the specific app.
        refs: The refs to resolve

    Returns:
        A mapping of Versions to the Refs.
    """
    if app_config.repo.type == RepositoryType.GITHUB:
        fetch_file = github_api.fetch_file
    elif app_config.repo.type == RepositoryType.HGMO:
        fetch_file = hgmo_api.fetch_file
    else:  # pragma: no cover
        assert False

    versions = {}

    for ref in refs:
        version_file_contents = fetch_file(
            app_config.repo.name, app_config.version_file.__root__.path, ref.resolved
        )

        v = parse_version_file(app_config.version_file, version_file_contents)

        versions[v] = ref

    return versions
