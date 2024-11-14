from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from django.core.checks import Error, register
from metric_config_parser.config import ConfigCollection
from metric_config_parser.segment import SegmentDefinition

from experimenter.experiments.constants import NimbusConstants


@dataclass
class MockCommit:
    committed_date: int


@dataclass
class MockRepository:
    git_dir: Path

    def iter_commits(self, *args, **kwargs):
        mock_commit = MockCommit(
            committed_date=int(datetime.now().timestamp()),
        )
        yield mock_commit


@dataclass
class Segment:
    slug: str
    friendly_name: str
    application: str
    description: str
    select_expression: str


class Segments:
    _segments = None

    @classmethod
    def _load_segments(
        cls, segment_data: dict[str, list[SegmentDefinition]] | None = None
    ):
        segments: list[Segment] = []

        app_name_application_config = {
            a.app_name: a for a in NimbusConstants.APPLICATION_CONFIGS.values()
        }

        config_collection = None
        if segment_data is None:
            repo_git_dir = Path("/experimenter/experimenter/segments/metric-hub-main")
            path = "metric-hub-main"

            mock_repo = MockRepository(git_dir=repo_git_dir)

            config_collection = ConfigCollection.from_local_repo(
                repo=mock_repo, path=path, is_private=False, main_branch="main"
            )

        for app_name, app_config in app_name_application_config.items():
            if segment_data is None:
                app_segments = (
                    config_collection.get_segments_for_app(app_name)
                    if config_collection
                    else []
                )
            else:
                app_segments = segment_data.get(app_name, [])

            for segment in app_segments:
                if isinstance(segment, SegmentDefinition):
                    segments.append(
                        Segment(
                            slug=segment.name,
                            friendly_name=segment.friendly_name,
                            application=app_config.slug,
                            description=segment.description,
                            select_expression=segment.select_expression,
                        )
                    )
                else:
                    raise TypeError(
                        f"Expected SegmentDefinition, got {type(segment).__name__}"
                    )

        return segments

    @classmethod
    def clear_cache(cls):
        cls._segments = None

    @classmethod
    def all(cls, segment_data: dict[str, list[SegmentDefinition]] | None = None):
        if cls._segments is None:
            cls._segments = cls._load_segments(segment_data)
        return cls._segments

    @classmethod
    def by_application(
        cls,
        application,
        segment_data: dict[str, list[SegmentDefinition]] | None = None,
    ):
        return [o for o in cls.all(segment_data) if o.application == application]


@register()
def check_segments(
    app_configs,
    segment_data: dict[str, list[SegmentDefinition]] | None = None,
    **kwargs,
):
    errors = []

    try:
        Segments.all(segment_data=segment_data)
    except Exception as e:
        errors.append(Error(f"Error loading Segments: {e}"))
    return errors
