from pathlib import Path
from subprocess import check_call

from manifesttool.appconfig import AppConfig

NIMBUS_CLI_PATH = "/application-services/bin/nimbus-cli"


def nimbus_cli(*args: list[str]):
    """Run nimbus-cli with the given arguments."""
    print("nimbus-cli", " ".join(args))
    check_call(
        [
            NIMBUS_CLI_PATH,
            *args,
        ]
    )


def download_single_file(
    app_config: AppConfig,
    channel: str,
    manifests_dir: Path,
):  # pragma: no cover
    """Download the single-file FML manifest for the app on the specified channel."""
    nimbus_cli(
        "fml",
        "--",
        "single-file",
        "--channel",
        channel,
        f"@{app_config.repo}/{app_config.fml_path}",
        str(manifests_dir / app_config.slug / f"{channel}.fml.yaml"),
    )


def generate_experimenter_yaml(app_config: AppConfig, manifests_dir: Path):
    """Generate an experimenter.yaml manifest from a single-file FML file."""
    default_channel = app_config.channels[0]
    nimbus_cli(
        "fml",
        "--",
        "generate-experimenter",
        str(manifests_dir / app_config.slug / f"{default_channel}.fml.yaml"),
        str(manifests_dir / app_config.slug / "experimenter.yaml"),
    )
