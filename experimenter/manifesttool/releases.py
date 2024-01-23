from typing import Optional

from manifesttool import github_api, hgmo_api
from manifesttool.appconfig import (
    AppConfig,
    BranchedDiscoveryStrategy,
    RepositoryType,
    TaggedDiscoveryStrategy,
)
from manifesttool.repository import Ref
from manifesttool.version import (
    Version,
    filter_versioned_refs,
    find_versioned_refs,
    resolve_ref_versions,
)


def _filter_ignored_versions(
    app_name: str,
    versions: dict[Version, Ref],
    ignored_versions: Optional[list[Version]],
):
    if ignored_versions:
        for ignored_version in ignored_versions:
            try:
                ref = versions.pop(ignored_version)
                print(f"fetch: {app_name}: Ignored version {ignored_version} at {ref}")
            except KeyError:
                pass


def discover_tagged_releases(
    app_name: str, app_config: AppConfig, strategy: TaggedDiscoveryStrategy
) -> dict[Version, Ref]:
    """Discover releases based on release branches and tags.

    Only the most recent 5 major versions of releases will be returned.
    """
    assert app_config.repo.type == RepositoryType.GITHUB

    # Find all release branches.
    branches = github_api.get_branches(app_config.repo.name)
    versions = find_versioned_refs(
        branches,
        strategy.branch_re,
        strategy.ignored_branches,
    )

    _filter_ignored_versions(app_name, versions, strategy.ignored_versions)

    # Limit to the last 5 major versions.
    #
    # We must pass a list here because if max() is passed a single arg it will
    # try to iterate over it.
    max_major_version = max([0, *(v.major for v in versions)])

    if max_major_version == 0:
        raise Exception(f"Could not find a major release for {app_name}.")

    min_version = Version(max_major_version - 4, 0, 0)

    versions = filter_versioned_refs(versions, min_version)

    # Extract the actual version number for each branch's version file.
    # Otherwise, e.g., a branch like release/v1 would end up overwriting 1.0.0
    # version constantly, even though it is likely futher ahead than 1.0.0.
    versions = resolve_ref_versions(app_config, versions.values())

    if strategy.tag_re:
        tags = github_api.get_tags(app_config.repo.name)
        tag_versions = find_versioned_refs(tags, strategy.tag_re, strategy.ignored_tags)
        tag_versions = filter_versioned_refs(tag_versions, min_version)

        _filter_ignored_versions(app_name, tag_versions, strategy.ignored_versions)

        versions.update(tag_versions)

    return versions


def discover_branched_releases(
    app_name: str,
    app_config: AppConfig,
    strategy: BranchedDiscoveryStrategy,
) -> dict[Version, Ref]:
    if app_config.repo.type == RepositoryType.GITHUB:
        resolve_branch = github_api.resolve_branch
    elif app_config.repo.type == RepositoryType.HGMO:
        resolve_branch = hgmo_api.resolve_branch
    else:  # pragma: no cover
        raise AssertionError()

    # If there are no branches listed, we will only scan the default branch.
    branches = strategy.branches
    if branches is None:
        branches = [app_config.repo.default_branch]

    refs = [resolve_branch(app_config.repo.name, branch) for branch in branches]

    return resolve_ref_versions(app_config, refs)
