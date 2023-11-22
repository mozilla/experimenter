import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from manifesttool import github_api
from manifesttool.appconfig import AppConfig, RepositoryType
from manifesttool.version import Version

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


def get_channels(app_config: AppConfig, fml_path: str, ref: str) -> list[str]:
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
            f"@{app_config.repo.name}/{fml_path}",
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
    manifest_dir: Path,
    app_config: AppConfig,
    fml_path: str,
    channel: str,
    ref: str,
    version: Optional[Version],
):
    """Download the single-file FML manifest for the app on the specified
    channel.

    If the AppConfig provides multiple FML paths, they will be tried in order.
    """
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
            f"@{app_config.repo.name}/{fml_path}",
            str(_get_fml_path(manifest_dir, app_config, channel, version)),
        ],
    )


def generate_experimenter_yaml(
    manifest_dir: Path,
    app_config: AppConfig,
    channel: str,
    version: Optional[Version],
):
    """Generate an experimenter.yaml manifest from a single-file FML file."""
    nimbus_cli(
        [
            "fml",
            "--",
            "generate-experimenter",
            str(_get_fml_path(manifest_dir, app_config, channel, version)),
            str(_get_experimenter_yaml_path(manifest_dir, app_config, version)),
        ],
    )


def _get_fml_path(
    manifest_dir: Path,
    app_config: AppConfig,
    channel: str,
    version: Optional[Version],
) -> Path:
    path = manifest_dir / app_config.slug

    if version:
        path /= f"v{version}"

    path.mkdir(exist_ok=True)

    return path / f"{channel}.fml.yaml"


def _get_experimenter_yaml_path(
    manifest_dir: Path,
    app_config: AppConfig,
    version: Optional[Version],
) -> Path:
    path = manifest_dir / app_config.slug

    if version:
        path /= f"v{version}"

    path.mkdir(exist_ok=True)

    return path / "experimenter.yaml"
