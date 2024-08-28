from dataclasses import dataclass

import toml
from django.conf import settings
from django.core.checks import Error, register

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
    def _load_segments(cls):
        segments: list[Segment] = []

        app_name_application_config = {
            a.app_name: a for a in NimbusConstants.APPLICATION_CONFIGS.values()
        }
        paths = [
            settings.JETSTREAM_CONFIG_SEGMENTS_PATH,
            settings.DEFINITIONS_CONFIG_SEGMENTS_PATH,
        ]

        for path in paths:
            for segment_file in path.iterdir():
                if segment_file.is_file() and segment_file.suffix == ".toml":

                    app_name = segment_file.stem

                    with segment_file.open() as f:
                        segment_toml = f.read()
                        segment_data = toml.loads(segment_toml)

                        if "segments" in segment_data:
                            for slug, segment_info in segment_data["segments"].items():

                                if not slug or slug == "data_sources":
                                    continue

                                segments.append(
                                    Segment(
                                        slug=slug,
                                        friendly_name=segment_info["friendly_name"],
                                        application=app_name_application_config[
                                            app_name
                                        ].slug,
                                        description=segment_info["description"],
                                        select_expression=segment_info[
                                            "select_expression"
                                        ],
                                    )
                                )

        return segments

    @classmethod
    def clear_cache(cls):
        cls._segments = None

    @classmethod
    def all(cls):
        if cls._segments is None:
            cls._segments = cls._load_segments()
        return cls._segments

    @classmethod
    def by_application(cls, application):
        return [o for o in cls.all() if o.application == application]


@register()
def check_segment_tomls(app_configs, **kwargs):
    errors = []

    try:
        Segments.all()
    except Exception as e:
        errors.append(Error(f"Error loading Segment TOMLS: {e}"))
    return errors
