import sys
from dataclasses import dataclass
from pathlib import Path

import click

from manifesttool import github_api, nimbus_cli
from manifesttool.appconfig import AppConfigs

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

    for app_name, app_config in context.app_configs.__root__.items():
        context.manifest_dir.joinpath(app_config.slug).mkdir(exist_ok=True)

        # We could operate against "main" for all these calls, but the
        # repository state might change between subsequent calls. That would
        # mean the generated single file manifests could differ because they
        # were based on different commits.
        ref = github_api.get_main_ref(app_config.repo)

        channels = nimbus_cli.get_channels(app_config, ref)

        if not channels:
            print(
                f"WARNING: Application {app_name} does not have any channels!",
                file=sys.stderr,
            )
            continue

        for channel in channels:
            nimbus_cli.download_single_file(
                app_config,
                channel,
                context.manifest_dir,
                ref,
            )

        # The single-file fml file for each channel will generate the same
        # experimenter.yaml, so we can pick any here.
        nimbus_cli.generate_experimenter_yaml(
            app_config,
            channels[0],
            context.manifest_dir,
        )
