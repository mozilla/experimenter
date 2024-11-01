from dataclasses import dataclass

from django.core.checks import Error, register
from metric_config_parser.config import ConfigCollection
from metric_config_parser.segment import SegmentDefinition

from experimenter.experiments.constants import NimbusConstants


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
    def _load_segments(cls, segment_data=None):
        segments: list[Segment] = []

        app_name_application_config = {
            a.app_name: a for a in NimbusConstants.APPLICATION_CONFIGS.values()
        }

        config_collection = None
        if segment_data is None:
            config_collection = ConfigCollection.from_github_repos(
                [
                    "https://github.com/mozilla/metric-hub",
                ]
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
    def all(cls, segment_data=None):
        if cls._segments is None:
            cls._segments = cls._load_segments(segment_data)
        return cls._segments

    @classmethod
    def by_application(cls, application, segment_data=None):
        return [o for o in cls.all(segment_data) if o.application == application]


@register()
def check_segments(app_configs, segments_data=None, **kwargs):
    errors = []

    try:
        Segments.all(segment_data=segments_data)
    except Exception as e:
        errors.append(Error(f"Error loading Segments: {e}"))
    return errors
