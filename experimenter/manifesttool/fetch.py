import sys
from dataclasses import dataclass
from pathlib import Path
from traceback import print_exception
from typing import Optional

import yaml
from mozilla_nimbus_schemas import FeatureManifest

from manifesttool import github_api, hgmo_api, nimbus_cli
from manifesttool.appconfig import AppConfig, RepositoryType
from manifesttool.repository import Ref
from manifesttool.version import (
    Version,
    filter_versioned_refs,
    find_versioned_refs,
    resolve_ref_versions,
)


@dataclass
class FetchResult:
    app_name: str
    ref: Ref
    version: Optional[Version]
    exc: Optional[Exception] = None

    def __str__(self):
        as_str = f"{self.app_name} at {self.ref} version {self.version}"
        if self.exc:
            exc_message = str(self.exc).partition("\n")[0]
            as_str = f"{as_str}\n{exc_message}\n"

        return as_str


def fetch_fml_app(
    manifest_dir: Path,
    app_name: str,
    app_config: AppConfig,
    ref: Optional[Ref] = None,
    version: Optional[Version] = None,
) -> FetchResult:
    if app_config.repo.type == RepositoryType.HGMO:
        raise Exception("FML-based apps on hg.mozilla.org are not supported.")

    if ref is not None and not ref.is_resolved:
        raise ValueError(f"fetch_fml_app: ref `{ref.name}` is not resolved")

    if version is not None and ref is None:
        raise ValueError("Cannot fetch specific version without a ref.")

    result = FetchResult(app_name=app_name, ref=ref or Ref("main"), version=version)

    try:
        # We could operate against "main" for all these calls, but the repository
        # state might change between subsequent calls. That would mean the generated
        # single file manifests could differ because they were based on different
        # commits.
        if ref is None:
            ref = result.ref = github_api.get_main_ref(app_config.repo.name)

        if version:
            print(f"fetch: {app_name} at {ref} version {version}")
        else:
            print(f"fetch: {app_name} at {ref}")

        channels = nimbus_cli.get_channels(app_config, ref.resolved)
        print(f"fetch: {app_name}: channels are {', '.join(channels)}")

        if not channels:
            print(
                f"WARNING: Application {app_name} does not have any channels!",
                file=sys.stderr,
            )
            raise Exception("No channels found")

        for channel in channels:
            print(f"fetch: {app_name}: download {channel} manifest")
            nimbus_cli.download_single_file(
                manifest_dir,
                app_config,
                channel,
                ref.resolved,
                version,
            )

        print(f"fetch: {app_name}: generate experimenter.yaml")
        # The single-file fml file for each channel will generate the same
        # experimenter.yaml, so we can pick any here.
        nimbus_cli.generate_experimenter_yaml(
            manifest_dir,
            app_config,
            channels[0],
            version,
        )
    except Exception as e:
        print_exception(e, file=sys.stderr)
        result.exc = e

    return result


def fetch_legacy_app(
    manifest_dir: Path,
    app_name: str,
    app_config: AppConfig,
    ref: Optional[Ref] = None,
    version: Optional[Version] = None,
) -> FetchResult:
    if app_config.repo.type == RepositoryType.GITHUB:
        raise Exception("Legacy experimenter.yaml apps on GitHub are not supported.")

    if ref is not None and not ref.is_resolved:
        raise ValueError(f"fetch_legacy_app: ref {ref.name} is not resolved")

    if version is not None and ref is None:
        raise ValueError("Cannot fetch specific version without a ref.")

    result = FetchResult(app_name=app_name, ref=ref or Ref("tip"), version=version)

    try:
        # We could operate against "tip" for all these calls, but the repository
        # state might change between subsequent calls. That would mean the fetched
        # feature schemas could differ or not be present if they were removed in a
        # subsequent commit.
        if ref is None:
            ref = result.ref = hgmo_api.get_tip_rev(app_config.repo.name)

        if version:
            print(f"fetch: {app_name} at {ref} version {version}")
        else:
            print(f"fetch: {app_name} at {ref}")

        print(f"fetch: {app_name}: downloading experimenter.yaml")

        app_dir = manifest_dir / app_config.slug
        if version:
            app_dir /= f"v{version}"

        app_dir.mkdir(exist_ok=True)
        manifest_path = app_dir / "experimenter.yaml"

        hgmo_api.fetch_file(
            app_config.repo.name,
            app_config.experimenter_yaml_path,
            ref.resolved,
            manifest_path,
        )

        with manifest_path.open() as f:
            raw_manifest = yaml.safe_load(f)
            manifest = FeatureManifest.parse_obj(raw_manifest)

        schema_dir = app_dir / "schemas"
        schema_dir.mkdir(exist_ok=True)

        # Some features may re-use the same schemas, so we only have to fetch them
        # once.
        fetched_schemas = set()

        for feature_slug, feature in manifest.__root__.items():
            feature = feature.__root__

            if feature.json_schema is not None:
                if feature.json_schema.path in fetched_schemas:
                    print(
                        f"fetch: {app_name}: already fetched schema for "
                        f"feature {feature_slug} ({feature.json_schema.path})"
                    )
                    continue

                print(
                    f"fetch: {app_name}: fetching schema for feature {feature_slug} "
                    f"({feature.json_schema.path})"
                )

                schema_path = schema_dir.joinpath(*feature.json_schema.path.split("/"))
                schema_path.parent.mkdir(exist_ok=True, parents=True)

                hgmo_api.fetch_file(
                    app_config.repo.name,
                    feature.json_schema.path,
                    ref.resolved,
                    schema_path,
                )

                fetched_schemas.add(feature.json_schema.path)
    except Exception as e:
        print_exception(e, file=sys.stderr)
        result.exc = e

    return result


def fetch_releases(
    manifest_dir: Path,
    app_name: str,
    app_config: AppConfig,
) -> list[FetchResult]:
    """Fetch all releases in the past 5 major versions of the app."""
    results = []

    if app_config.repo.type == RepositoryType.HGMO:
        raise Exception("Cannot fetch releases for apps hosted on hg.mozilla.org.")

    if app_config.fml_path is None:
        raise Exception("Cannot fetch releases for legacy apps.")

    if app_config.version_file is None:
        raise Exception(f"App {app_name} does not have a version file.")

    if not app_config.branch_re:
        print(f"fetch: releases: {app_name} does not support releases", file=sys.stderr)
        return results

    # Find all release branches.
    branches = github_api.get_branches(app_config.repo.name)
    versions = find_versioned_refs(
        branches, app_config.branch_re, app_config.ignored_branches
    )

    # Limit to the last 5 major versions.
    #
    # We must pass a list here because if max() is passed a single arg it will
    # try to iterate over it.
    max_major_version = max([0, *(v.major for v in versions.keys())])

    if max_major_version == 0:
        raise Exception(f"Could not find a major release for {app_name}.")

    min_version = Version(max_major_version - 4, 0, 0)

    versions = filter_versioned_refs(versions, min_version)

    # Extract the actual version number for each branch's version file.
    # Otherwise, e.g., a branch like release/v1 would end up overwriting 1.0.0
    # version constantly, even though it is likely futher ahead than 1.0.0.
    versions = resolve_ref_versions(app_config, versions.values())

    if app_config.tag_re:
        tags = github_api.get_tags(app_config.repo.name)
        tag_versions = find_versioned_refs(
            tags, app_config.tag_re, app_config.ignored_tags
        )
        tag_versions = filter_versioned_refs(tag_versions, min_version)

        versions.update(tag_versions)

    for version, ref in versions.items():
        results.append(fetch_fml_app(manifest_dir, app_name, app_config, ref, version))

    return results


def summarize_results(results: list[FetchResult]):
    print("\n\nSUMMARY:\n")

    if any(result.exc is None for result in results):
        print("SUCCESS:\n")
        for result in results:
            if result.exc is None:
                print(result)

        print("")

    if any(result.exc is not None for result in results):
        print("FAILURES:\n")
        for result in results:
            if result.exc is not None:
                print(result)
