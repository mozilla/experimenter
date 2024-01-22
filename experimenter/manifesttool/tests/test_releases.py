from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import TestCase
from unittest.mock import patch

import responses
from parameterized import parameterized

import manifesttool
from manifesttool.appconfig import (
    AppConfig,
    DiscoveryStrategy,
    ReleaseDiscovery,
    Repository,
    RepositoryType,
    TaggedDiscoveryStrategy,
    VersionFile,
    VersionFileType,
)
from manifesttool.releases import discover_branched_releases, discover_tagged_releases
from manifesttool.repository import Ref
from manifesttool.tests.test_fetch import make_mock_fetch_file
from manifesttool.version import Version


@contextmanager
def mocks_for_discover_tagged_releases(
    app_config: AppConfig,
    strategy: TaggedDiscoveryStrategy,
    branches: list[Ref],
    tags: Optional[list[Ref]],
    ref_versions: dict[str, Version],
):
    """Create a set of mocks to call ``fetch_releases``.

    Args:
        app_config:
            The app configuration.

        strategy:
            The strategy that will be used to create the mocks.

            If ``tag_re`` is not specified, then ``tags`` must be ``None``.

        branches:
            The list of refs to return from ``get_branches()``.

        Tags:
            The list of refs to return from ``get_tags()``.

            If ``None``, ``strategy.tag_re`` must also be ``None``.

        ref_versions:
            A mapping of resolved refs to Versions.

            This argument is used to generate a mock for ``fetch_file()``.

    Yields:
        A 3-tuple of the mocks for ``get_branches``, ``get_tags``, and ``fetch_file``.
    """
    assert app_config.repo.type == RepositoryType.GITHUB
    assert strategy.branch_re is not None

    # Mocking plist files is more annoying.
    assert app_config.release_discovery is not None
    assert (
        app_config.release_discovery.version_file.__root__.type
        == VersionFileType.PLAIN_TEXT
    )

    # Ensure tags are defined if app specifies a tag regex.
    assert strategy.tag_re is None or tags is not None

    def mock_get_branches(*args):
        return branches

    def mock_get_tags(*args):
        assert tags is not None
        return tags

    def mock_fetch_file(
        repo: str, path: str, ref: str, download_path: Optional[Path] = None
    ):
        assert repo == app_config.repo.name
        assert download_path is None
        assert path == app_config.release_discovery.version_file.__root__.path
        assert ref in ref_versions

        return str(ref_versions[ref])

    with (
        patch.object(
            manifesttool.github_api, "get_branches", side_effect=mock_get_branches
        ) as get_branches,
        patch.object(
            manifesttool.github_api, "get_tags", side_effect=mock_get_tags
        ) as get_tags,
        patch.object(
            manifesttool.github_api, "fetch_file", side_effect=mock_fetch_file
        ) as fetch_file,
    ):
        yield (
            get_branches,
            get_tags,
            fetch_file,
        )


def make_mock_resolve_branch(refs: dict[str, str]):
    def resolve_branch(repo: str, bookmark: str):
        return Ref(bookmark, refs[bookmark])

    return resolve_branch


class ReleaseTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use responses to ensure we don't make any HTTP calls.
        responses.start()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        responses.stop()

    def test_discover_tagged_releases(self):
        """Testing discover_tagged_releases."""
        strategy = DiscoveryStrategy.create_tagged(
            branch_re=r"release_v(?P<major>\d)+",
            tag_re=r"v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
        )
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[strategy],
            ),
        )

        branches = [Ref(f"release_v{major}", f"branch-v{major}") for major in range(1, 7)]
        tags = [Ref(f"v{major}.0.0", f"tag-v{major}") for major in range(1, 7)]
        ref_versions = {
            **{f"branch-v{major}": Version(major, 0, 1) for major in range(1, 7)},
            **{f"tag-v{major}": Version(major) for major in range(1, 7)},
        }

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with mocks_for_discover_tagged_releases(
                app_config, strategy.__root__, branches, tags, ref_versions
            ):
                releases = discover_tagged_releases("app", app_config, strategy.__root__)

        self.assertEqual(
            releases,
            {
                **{
                    Version(major, 0, 1): Ref(f"release_v{major}", f"branch-v{major}")
                    for major in range(2, 7)
                },
                **{
                    Version(major): Ref(f"v{major}.0.0", f"tag-v{major}")
                    for major in range(2, 7)
                },
            },
        )

    def test_discover_tagged_releases_ignored_versions(self):
        """Testing discover_tagged_releases with an ignored version."""
        strategy = DiscoveryStrategy.create_tagged(
            branch_re=r"release_v(?P<major>\d)+",
            tag_re=r"v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
            ignored_versions=[
                Version(2),
                Version(2, 1, 2),
                Version(2, 3, 9),
            ],
        )
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[strategy],
            ),
        )

        branches = [Ref(f"release_v{major}", f"branch-v{major}") for major in (1, 2, 3)]

        tags = [
            Ref(f"v{major}.{minor}.{patch}", f"tag-v{major}.{minor}.{patch}")
            for major in (1, 2, 3)
            for minor in (0, 1, 2, 3)
            for patch in (0, 1, 2, 3)
        ]

        ref_versions = {
            **{f"branch-v{major}": Version(major, 3, 9) for major in (1, 2, 3)},
            **{
                f"tag-v{major}.{minor}.{patch}": Version(major, minor, patch)
                for major in (1, 2, 3)
                for minor in (0, 1, 2, 3)
                for patch in (0, 1, 2, 3)
            },
        }

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with mocks_for_discover_tagged_releases(
                app_config,
                strategy.__root__,
                branches,
                tags,
                ref_versions,
            ):
                releases = discover_tagged_releases("app", app_config, strategy.__root__)

            self.assertEqual(
                releases,
                {
                    **{
                        Version(major, 3, 9): Ref(f"release_v{major}", f"branch-v{major}")
                        for major in (1, 3)
                    },
                    **{
                        Version(major, minor, patch): Ref(
                            f"v{major}.{minor}.{patch}", f"tag-v{major}.{minor}.{patch}"
                        )
                        for major in (1, 2, 3)
                        for minor in (0, 1, 2, 3)
                        for patch in (0, 1, 2, 3)
                        if (major, minor, patch)
                        not in (
                            (2, 0, 0),
                            (2, 1, 2),
                        )
                    },
                },
            )

    def test_fetch_releases_no_tag_re(self):
        """Testing discover_tagged_releases with no tag_re specified."""
        strategy = DiscoveryStrategy.create_tagged(branch_re=r"release_v(?P<major>\d)+")
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[strategy],
            ),
        )

        branches = [Ref(f"release_v{major}", f"branch-v{major}") for major in range(1, 7)]
        ref_versions = {f"branch-v{major}": Version(major, 0, 1) for major in range(1, 7)}

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with mocks_for_discover_tagged_releases(
                app_config, strategy.__root__, branches, None, ref_versions
            ) as (
                get_branches,
                get_tags,
                resolve_ref_versions,
            ):
                releases = discover_tagged_releases("app", app_config, strategy.__root__)

                get_tags.assert_not_called()

        self.assertEqual(
            releases,
            {
                Version(major, 0, 1): Ref(f"release_v{major}", f"branch-v{major}")
                for major in range(2, 7)
            },
        )

    @patch.object(manifesttool.releases.github_api, "get_branches", lambda *args: [])
    def test_fetch_releases_no_major_release(self):
        """Testing fetch_releases when there are no release branches."""
        strategy = DiscoveryStrategy.create_tagged(
            branch_re=r"release_v(?P<major>\d)+",
            tag_re=r"v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
        )
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[strategy],
            ),
        )

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with self.assertRaisesRegex(
                Exception, "Could not find a major release for app."
            ):
                discover_tagged_releases("app", app_config, strategy.__root__)

    @parameterized.expand(
        [
            (
                AppConfig(
                    slug="fml-app",
                    repo=Repository(
                        type=RepositoryType.GITHUB,
                        name="fml-repo",
                    ),
                    fml_path="nimbus.fml.yaml",
                    release_discovery=ReleaseDiscovery(
                        version_file=VersionFile.create_plain_text("version.txt"),
                        strategies=[
                            DiscoveryStrategy.create_branched(["foo", "bar", "baz"])
                        ],
                    ),
                ),
                manifesttool.releases.github_api,
            ),
            (
                AppConfig(
                    slug="legacy-app",
                    repo=Repository(
                        type=RepositoryType.HGMO,
                        name="legacy-repo",
                        default_branch="foo",
                    ),
                    experimenter_yaml_path="experimenter.yaml",
                    release_discovery=ReleaseDiscovery(
                        version_file=VersionFile.create_plain_text("version.txt"),
                        strategies=[
                            DiscoveryStrategy.create_branched(["foo", "bar", "baz"])
                        ],
                    ),
                ),
                manifesttool.releases.hgmo_api,
            ),
        ]
    )
    def test_discover_branched_releases(self, app_config: AppConfig, api):
        strategy = app_config.release_discovery.strategies[0].__root__
        app_name = app_config.slug.replace("-", "_")

        branches = {"foo": "1", "bar": "2", "baz": "3"}
        paths_by_ref = {
            "1": {"version.txt": "1.0.0"},
            "2": {"version.txt": "2.0.0"},
            "3": {"version.txt": "3.0.0"},
        }

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with (
                patch.object(
                    api,
                    "resolve_branch",
                    make_mock_resolve_branch(branches),
                ),
                patch.object(
                    api,
                    "fetch_file",
                    make_mock_fetch_file(paths_by_ref=paths_by_ref),
                ),
            ):
                releases = discover_branched_releases(app_name, app_config, strategy)

            self.assertEqual(
                releases,
                {
                    Version(1): Ref("foo", "1"),
                    Version(2): Ref("bar", "2"),
                    Version(3): Ref("baz", "3"),
                },
            )

    @patch.object(
        manifesttool.releases.hgmo_api,
        "resolve_branch",
        side_effect=make_mock_resolve_branch(
            {
                "default": "1",
            }
        ),
    )
    @patch.object(
        manifesttool.releases.hgmo_api,
        "fetch_file",
        make_mock_fetch_file(
            paths_by_ref={
                "1": {"version.txt": "1.0.0"},
            }
        ),
    )
    def test_discover_branched_releases_default(self, resolve_branch):
        strategy = DiscoveryStrategy.create_branched()
        app_config = AppConfig(
            slug="legacy-app",
            repo=Repository(
                type=RepositoryType.HGMO,
                name="legacy-repo",
                default_branch="default",
            ),
            experimenter_yaml_path="experimenter.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[strategy],
            ),
        )

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            releases = discover_branched_releases(
                "legacy_app", app_config, strategy.__root__
            )

            self.assertEqual(
                releases,
                {
                    Version(1): Ref("default", "1"),
                },
            )

        resolve_branch.assert_called_once_with(app_config.repo.name, "default")
