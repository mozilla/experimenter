import json
import subprocess
import sys
from pathlib import Path

from manifesttool.appconfig import AppConfig, RepositoryType

NIMBUS_CLI_PATH = "/application-services/bin/nimbus-cli"


def nimbus_cli(args: list[str], *, output: bool = False):
    """Run nimbus-cli with the given arguments."""
    print("nimbus-cli", " ".join(args))
    method = subprocess.check_output if output else subprocess.check_call

    return method(
        [
            NIMBUS_CLI_PATH,
            *args,
        ]
    )


def get_channels(app_config: AppConfig, ref: str) -> list[str]:
    """Get the list of channels supported by the application."""
    assert app_config.repo.type == RepositoryType.GITHUB
    output = nimbus_cli(
        [
            "fml",
            "--",
            "channels",
            "--json",
            "--ref",
            ref,
            f"@{app_config.repo.name}/{app_config.fml_path}",
        ],
        output=True,
    )

    try:
        return json.loads(output)
    except Exception as e:
        print(
            f"Could not parse JSON output from nimbus-cli: {e}\n"
            f"nimbus-cli output:\n\n{output}",
            file=sys.stderr,
        )
        raise


def download_single_file(
    app_config: AppConfig,
    channel: str,
    manifests_dir: Path,
    ref: str,
):
    """Download the single-file FML manifest for the app on the specified channel."""
    assert app_config.repo.type == RepositoryType.GITHUB
    nimbus_cli(
        [
            "fml",
            "--",
            "single-file",
            "--channel",
            channel,
            "--ref",
            ref,
            f"@{app_config.repo.name}/{app_config.fml_path}",
            str(manifests_dir / app_config.slug / f"{channel}.fml.yaml"),
        ],
    )


def generate_experimenter_yaml(app_config: AppConfig, channel: str, manifests_dir: Path):
    """Generate an experimenter.yaml manifest from a single-file FML file."""
    nimbus_cli(
        [
            "fml",
            "--",
            "generate-experimenter",
            str(manifests_dir / app_config.slug / f"{channel}.fml.yaml"),
            str(manifests_dir / app_config.slug / "experimenter.yaml"),
        ],
    )
