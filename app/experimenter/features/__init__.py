import json
import os
from enum import Enum
from typing import Literal, Optional, Union

from django.conf import settings
from django.core.checks import Error, register
from pydantic import BaseModel

from experimenter.experiments.constants import NimbusConstants


class FeatureVariableType(Enum):
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"


class FeatureVariable(BaseModel):
    description: Optional[str]
    enum: Optional[list[str]]
    fallbackPref: Optional[str]
    type: Optional[FeatureVariableType]


class Feature(BaseModel):
    applicationSlug: str
    description: Optional[str]
    exposureDescription: Optional[Union[Literal[False], str]]
    isEarlyStartup: Optional[bool]
    slug: str
    variables: Optional[dict[str, FeatureVariable]]


class Features:
    _features = None

    @classmethod
    def _load_features(cls):
        features = []

        for application in NimbusConstants.APPLICATION_CONFIGS.values():
            application_json_path = os.path.join(
                settings.FEATURE_MANIFESTS_PATH, f"{application.slug}.json"
            )

            if os.path.exists(application_json_path):
                with open(application_json_path) as application_json_file:
                    application_json_data = json.loads(application_json_file.read())
                    for feature_slug in application_json_data.keys():
                        feature_data = application_json_data[feature_slug]
                        feature_data["slug"] = feature_slug
                        feature_data["applicationSlug"] = application.slug
                        features.append(Feature.parse_obj(feature_data))

        return features

    @classmethod
    def clear_cache(cls):
        cls._features = None

    @classmethod
    def all(cls):
        if cls._features is None:
            cls._features = cls._load_features()

        return cls._features

    @classmethod
    def by_application(cls, application):
        return [f for f in cls.all() if f.applicationSlug == application]


@register()
def check_features(app_configs, **kwargs):
    errors = []

    try:
        Features.all()
    except Exception as e:
        errors.append(Error(f"Error loading feature data {e}"))
    return errors
