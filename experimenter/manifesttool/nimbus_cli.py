import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from manifesttool.appconfig import AppConfig, Repository, RepositoryType
from manifesttool.repository import Ref
from manifesttool.version import Version

NIMBUS_CLI_PATH = "/application-services/bin/nimbus-cli"


def nimbus_cli(args: list[str]) -> bytes:
    """Run nimbus-cli with the given arguments."""
    print("nimbus-cli", " ".join(args))

    return subprocess.check_output(
        [
            NIMBUS_CLI_PATH,
            *args,
        ],
        stderr=subprocess.PIPE,
    )


def _assert_ref_xor_github_repo(repo_type: RepositoryType, ref: Optional[Ref]):
    if repo_type == RepositoryType.GITHUB and ref is None:
        raise AssertionError("GitHub repositories require a ref")

    if repo_type == RepositoryType.LOCAL and ref is not None:
        raise AssertionError("local repositories do not support specific refs")


def _repo_path_cli_args(repo: Repository, ref: Optional[Ref], fml_path: str) -> list[str]:
    """Return the appropriate arguments to pass to nimbus-cli to refer to a
    local or remote (i.e., GitHub) FML file.
    """
    _assert_ref_xor_github_repo(repo.type, ref)

    match repo.type:
        case RepositoryType.LOCAL:
            return [fml_path]

        case RepositoryType.GITHUB:
            return [
                "--ref",
                ref.target,
                f"@{repo.name}/{fml_path}",
            ]


def get_channels(app_config: AppConfig, fml_path: str, ref: Optional[Ref]) -> list[str]:
    """Get the list of channels supported by the application."""

    output = nimbus_cli(
        [
            "fml",
            "--",
            "channels",
            "--json",
            *_repo_path_cli_args(app_config.repo, ref, fml_path),
        ]
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
    ref: Optional[Ref],
    version: Optional[Version],
):
    """Download the single-file FML manifest for the app on the specified
    channel.
    """
    nimbus_cli(
        [
            "fml",
            "--",
            "single-file",
            "--channel",
            channel,
            *_repo_path_cli_args(app_config.repo, ref, fml_path),
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
