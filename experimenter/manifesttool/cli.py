import sys
from dataclasses import dataclass
from pathlib import Path

import click
import yaml
from mozilla_nimbus_schemas import FeatureManifest

from manifesttool import github_api, hgmo_api, nimbus_cli
from manifesttool.appconfig import AppConfig, AppConfigs, RepositoryType

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

        if app_config.fml_path is not None:
            fetch_fml_app(context, app_name, app_config)
        elif app_config.experimenter_yaml_path is not None:
            fetch_legacy_app(context, app_name, app_config)
        else:  # pragma: no cover
            assert False, "unreachable"


def fetch_fml_app(context: Context, app_name: str, app_config: AppConfig):
    if app_config.repo.type == RepositoryType.HGMO:
        raise Exception("FML-based apps on hg.mozilla.org are not supported.")

    # We could operate against "main" for all these calls, but the repository
    # state might change between subsequent calls. That would mean the generated
    # single file manifests could differ because they were based on different
    # commits.
    ref = github_api.get_main_ref(app_config.repo.name)
    print(f"fetch-latest: {app_name}: main is {ref}")

    channels = nimbus_cli.get_channels(app_config, ref)
    print(f"fetch-latest: {app_name}: channels are {', '.join(channels)}")

    if not channels:
        print(
            f"WARNING: Application {app_name} does not have any channels!",
            file=sys.stderr,
        )
        return

    for channel in channels:
        print(f"fetch-latest: {app_name}: download {channel} manifest")
        nimbus_cli.download_single_file(
            app_config,
            channel,
            context.manifest_dir,
            ref,
        )

    print(f"fetch-latest: {app_name}: generate experimenter.yaml")
    # The single-file fml file for each channel will generate the same
    # experimenter.yaml, so we can pick any here.
    nimbus_cli.generate_experimenter_yaml(
        app_config,
        channels[0],
        context.manifest_dir,
    )


def fetch_legacy_app(context: Context, app_name: str, app_config: AppConfig):
    if app_config.repo.type == RepositoryType.GITHUB:
        raise Exception("Legacy experimenter.yaml apps on GitHub are not supported.")

    # We could operate against "main" for all these calls, but the repository
    # state might change between subsequent calls. That would mean the fetched
    # feature schemas could differ or not be present if they were removed in a
    # subsequent commit.
    rev = hgmo_api.get_tip_rev(app_config.repo.name)
    print(f"fetch-latest: {app_name}: tip is {rev}")

    manifest_path = context.manifest_dir / app_config.slug / "experimenter.yaml"
    print(f"fetch-latest: {app_name}: downloading experimenter.yaml")
    hgmo_api.fetch_file(
        app_config.repo.name,
        app_config.experimenter_yaml_path,
        rev,
        context.manifest_dir / app_config.slug / "experimenter.yaml",
    )

    with manifest_path.open() as f:
        raw_manifest = yaml.safe_load(f)
        manifest = FeatureManifest.parse_obj(raw_manifest)

    schema_dir = context.manifest_dir / app_config.slug / "schemas"
    schema_dir.mkdir(exist_ok=True)

    # Some features may re-use the same schemas, so we only have to fetch them
    # once.
    fetched_schemas = set()

    for feature_slug, feature in manifest.__root__.items():
        feature = feature.__root__

        if feature.json_schema is not None:
            if feature.json_schema.path in fetched_schemas:
                print(
                    f"fetch-latest: {app_name}: already fetched schema for "
                    f"feature {feature_slug} ({feature.json_schema.path})"
                )
                continue

            print(
                f"fetch-latest: {app_name}: fetching schema for feature {feature_slug} "
                f"({feature.json_schema.path})"
            )

            schema_path = schema_dir.joinpath(*feature.json_schema.path.split("/"))
            schema_path.parent.mkdir(exist_ok=True, parents=True)

            hgmo_api.fetch_file(
                app_config.repo.name,
                feature.json_schema.path,
                rev,
                schema_path,
            )

            fetched_schemas.add(feature.json_schema.path)
