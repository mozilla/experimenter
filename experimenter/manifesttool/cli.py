from dataclasses import dataclass
from pathlib import Path

import click

from manifesttool.appconfig import AppConfigs
from manifesttool.fetch import fetch_fml_app, fetch_legacy_app, summarize_results

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
def fetch(ctx: click.Context):
    """Fetch the FML manifests and generate experimenter.yaml files."""
    context = ctx.find_object(Context)

    results = []

    for app_name, app_config in context.app_configs.__root__.items():
        context.manifest_dir.joinpath(app_config.slug).mkdir(exist_ok=True)

        if app_config.fml_path is not None:
            results.append(fetch_fml_app(context.manifest_dir, app_name, app_config))
        elif app_config.experimenter_yaml_path is not None:
            results.append(fetch_legacy_app(context.manifest_dir, app_name, app_config))
        else:  # pragma: no cover
            assert False, "unreachable"

    summarize_results(results)
