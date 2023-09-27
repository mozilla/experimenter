from dataclasses import dataclass
from pathlib import Path

import click

from manifesttool.appconfig import AppConfigs
from manifesttool.nimbus_cli import download_single_file, generate_experimenter_yaml

MANIFESTS_DIR = Path(__file__).parent.parent / "experimenter" / "features" / "manifests"


@dataclass
class Context:
    manifest_dir: Path
    app_configs: AppConfigs


@click.group()
@click.option(
    "--manifest-dir",
    type=Path,
    default=MANIFESTS_DIR,
    help="The directory that contains manifests",
)
@click.pass_context
def main(ctx: click.Context, *, manifest_dir: Path):
    """manifest-tool - tools for working with manifests of Experimenter apps."""

    apps_yaml_path = manifest_dir / "apps.yaml"
    app_configs = AppConfigs.load_from_file(apps_yaml_path)
    ctx.obj = Context(
        manifest_dir,
        app_configs,
    )


@main.command("fetch-latest")
@click.pass_context
def fetch_latest(ctx: click.Context):
    """Fetch the latest FML manifests and generate experimenter.yaml files."""

    context = ctx.find_object(Context)

    for app_config in context.app_configs.__root__.values():
        context.manifest_dir.joinpath(app_config.slug).mkdir(exist_ok=True)
        for channel in app_config.channels:
            download_single_file(
                app_config,
                channel,
                context.manifest_dir,
            )

        generate_experimenter_yaml(app_config, context.manifest_dir)
