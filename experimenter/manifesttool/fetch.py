import sys
from dataclasses import dataclass
from pathlib import Path
from traceback import print_exception
from typing import Optional, TextIO

import yaml
from mozilla_nimbus_schemas import FeatureManifest

from manifesttool import github_api, hgmo_api, nimbus_cli
from manifesttool.appconfig import AppConfig, DiscoveryStrategyType, RepositoryType
from manifesttool.releases import discover_branched_releases, discover_tagged_releases
from manifesttool.repository import Ref, RefCache
from manifesttool.version import Version


@dataclass
class FetchResult:
    app_name: str
    ref: Ref
    version: Optional[Version]
    exc: Optional[Exception] = None
    cached: bool = False

    def __str__(self):  # pragma: no cover
        as_str = f"{self.app_name} at {self.ref} version {self.version}"

        if self.exc:
            exc_message = str(self.exc).partition("\n")[0]
            as_str = f"{as_str}\n{exc_message}\n"
        elif self.cached:
            as_str = f"{as_str} (cached)"

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
            ref = result.ref = github_api.resolve_branch(
                app_config.repo.name, app_config.repo.default_branch
            )

        if version:
            print(f"fetch: {app_name} at {ref} version {version}")
        else:
            print(f"fetch: {app_name} at {ref}")

        if isinstance(app_config.fml_path, str):
            fml_path = app_config.fml_path
        elif isinstance(app_config.fml_path, list):
            for fml_path in app_config.fml_path:
                if github_api.file_exists(app_config.repo.name, fml_path, ref.target):
                    break
            else:
                raise Exception(
                    f"Could not find a feature manifest for {app_name} at {ref}"
                )

        channels = nimbus_cli.get_channels(app_config, fml_path, ref.target)
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
                fml_path,
                channel,
                ref.target,
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
            ref = result.ref = hgmo_api.resolve_branch(
                app_config.repo.name, app_config.repo.default_branch
            )

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
            ref.target,
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
                    ref.target,
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
    ref_cache: RefCache,
) -> list[FetchResult]:
    """Fetch all releases for the app."""
    results = []

    if app_config.release_discovery is None:
        raise Exception(f"App {app_name} does not support releases.")

    versions = {}
    for strategy in app_config.release_discovery.strategies:
        strategy = strategy.__root__
        if strategy.type == DiscoveryStrategyType.TAGGED:
            versions.update(discover_tagged_releases(app_name, app_config, strategy))
        elif strategy.type == DiscoveryStrategyType.BRANCHED:
            versions.update(discover_branched_releases(app_name, app_config, strategy))
        else:  # pragma: no cover
            raise AssertionError("unreachable")

    if app_config.fml_path:
        fetch_app = fetch_fml_app
    else:
        fetch_app = fetch_legacy_app

    for version, ref in versions.items():
        if ref_cache.get(ref.name) == ref:
            print(f"fetch: {app_name} at {ref.name} has not updated")
            results.append(FetchResult(app_name, ref, version, cached=True))
            continue

        result = fetch_app(manifest_dir, app_name, app_config, ref, version)

        if result.exc is None:
            ref_cache.add(ref)

        results.append(result)

    return results


def summarize_results(results: list[FetchResult], file: TextIO) -> (int, int, int):
    """Print out a summary of the results to the given file.

    Returns:
        A 3-tuple of the number of successes, the number of cache hits, and the
        number of failures.
    """
    successes = []
    failures = []
    cached = []

    for result in results:
        if result.exc:
            failures.append(result)
        elif result.cached:
            cached.append(result)
        else:
            successes.append(result)

    if file == sys.stdout:
        print("\n\n")

    print("SUMMARY:\n", file=file)

    if successes:
        print("SUCCESS:\n", file=file)
        for result in successes:
            print(result, file=file)

        print(file=file)

    if cached:
        print("CACHED:\n", file=file)
        for result in cached:
            print(result, file=file)

        print(file=file)

    if failures:
        print("FAILURES:\n", file=file)
        for result in failures:
            print(result, file=file)

    return (len(successes), len(cached), len(failures))
