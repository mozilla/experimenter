import json
import os
from enum import Enum
from typing import Literal, Optional, Union
from urllib.parse import urljoin

import requests
import yaml
from django.conf import settings
from django.core.checks import Error, register
from pydantic import BaseModel, Field

from experimenter.experiments.constants import NimbusConstants

MC_ROOT = "https://hg.mozilla.org/mozilla-central/raw-file/tip/"


class FeatureVariableType(Enum):
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"


FEATURE_SCHEMA_TYPES = {
    FeatureVariableType.INT: "integer",
    FeatureVariableType.STRING: "string",
    FeatureVariableType.BOOLEAN: "boolean",
}


class FeatureVariable(BaseModel):
    description: Optional[str]
    enum: Optional[list[str]]
    fallbackPref: Optional[str]
    type: Optional[FeatureVariableType]


class FeatureSchema(BaseModel):
    uri: Optional[str]
    path: Optional[str]


class Feature(BaseModel):
    applicationSlug: str
    description: Optional[str]
    exposureDescription: Optional[Union[Literal[False], str]]
    isEarlyStartup: Optional[bool]
    slug: str
    variables: Optional[dict[str, FeatureVariable]]
    schema_paths: Optional[FeatureSchema] = Field(alias="schema")

    def load_remote_jsonschema(self):
        schema_url = urljoin(MC_ROOT, self.schema_paths.path)
        schema_data = requests.get(schema_url).content
        return json.dumps(json.loads(schema_data), indent=2)

    def generate_jsonschema(self):
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

        for variable_slug, variable in self.variables.items():
            variable_schema = {
                "description": variable.description,
            }

            if variable.type in FEATURE_SCHEMA_TYPES:
                variable_schema["type"] = FEATURE_SCHEMA_TYPES[variable.type]

            if variable.enum:
                variable_schema["enum"] = variable.enum

            schema["properties"][variable_slug] = variable_schema

        return json.dumps(schema, indent=2)

    def get_jsonschema(self):
        if self.schema_paths is not None:
            return self.load_remote_jsonschema()
        return self.generate_jsonschema()


class Features:
    _features = None

    @classmethod
    def _load_features(cls):
        features = []

        for application in NimbusConstants.APPLICATION_CONFIGS.values():
            application_yaml_path = os.path.join(
                settings.FEATURE_MANIFESTS_PATH, f"{application.slug}.yaml"
            )

            if os.path.exists(application_yaml_path):
                with open(application_yaml_path) as application_yaml_file:
                    application_data = yaml.load(
                        application_yaml_file.read(), Loader=yaml.Loader
                    )
                    for feature_slug in application_data.keys():
                        feature_data = application_data[feature_slug]
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
