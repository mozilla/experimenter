import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click

from manifesttool.appconfig import AppConfigs
from manifesttool.fetch import (
    fetch_fml_app,
    fetch_legacy_app,
    fetch_releases,
    summarize_results,
)
from manifesttool.repository import RefCache

MANIFEST_DIR = Path(__file__).parent.parent / "experimenter" / "features" / "manifests"


@dataclass
class Context:
    manifest_dir: Path
    app_configs: AppConfigs


@click.group()
@click.option(
    "--manifest-dir",
    type=Path,
    default=MANIFEST_DIR,
    help="The directory that contains manifests",
)
@click.pass_context
def main(ctx: click.Context, *, manifest_dir: Path):
    """manifest-tool - tools for working with manifests of Experimenter apps."""
    app_configs = AppConfigs.load_from_directory(manifest_dir)
    ctx.obj = Context(
        manifest_dir,
        app_configs,
    )


@main.command("fetch")
@click.pass_context
@click.option(
    "--summary", "summary_filename", type=Path, help="Write a summary to this file."
)
@click.option(
    "--app",
    "app_names",
    type=str,
    multiple=True,
    help="Only fetch updates for the specified app(s).",
)
def fetch(ctx: click.Context, *, summary_filename: Optional[Path], app_names: list[str]):
    """Fetch the FML manifests and generate experimenter.yaml files."""
    context = ctx.find_object(Context)

    results = []

    if app_names:
        for app_name in app_names:
            if app_name not in context.app_configs.__root__.keys():
                print(f"fetch: unknown app {app_name}", file=sys.stderr)
                sys.exit(1)
    else:
        app_names = context.app_configs.__root__.keys()

    for app_name in app_names:
        app_config = context.app_configs.__root__[app_name]

        app_dir = context.manifest_dir.joinpath(app_config.slug)
        app_dir.mkdir(exist_ok=True)

        if app_config.fml_path is not None:
            results.append(fetch_fml_app(context.manifest_dir, app_name, app_config))
        elif app_config.experimenter_yaml_path is not None:
            results.append(fetch_legacy_app(context.manifest_dir, app_name, app_config))
        else:  # pragma: no cover
            assert False, "unreachable"

        if app_config.release_discovery:
            ref_cache_path = app_dir / ".ref-cache.yaml"
            ref_cache = RefCache.load_or_create(ref_cache_path)

            results.extend(
                fetch_releases(context.manifest_dir, app_name, app_config, ref_cache)
            )

            ref_cache.write_to_file(ref_cache_path)

    summary_file = sys.stdout
    if summary_filename:
        summary_file = summary_filename.open("w")

    success_count, cache_count, fail_count = summarize_results(results, summary_file)

    if summary_filename:
        summary_file.close()

    # If we have any successful results, we'll exit normally. In CI, the PR will
    # include the generated summary, which will contain any failures.
    #
    # However, if all we have are failures and cache hits, we won't produce a
    # PR. Therefore we should exit(1) and cause the task to fail so it will be
    # noticed.
    if fail_count > 0 and success_count == 0:
        raise SystemExit(1)
