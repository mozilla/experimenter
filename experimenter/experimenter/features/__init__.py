import json
import os
from enum import Enum
from typing import Literal

import yaml
from django.conf import settings
from django.core.checks import Error, register
from pydantic import BaseModel, Field

from experimenter.experiments.constants import NimbusConstants


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

FEATURE_PYTHON_TYPES = {
    FeatureVariableType.INT: int,
    FeatureVariableType.STRING: str,
    FeatureVariableType.BOOLEAN: bool,
}


class FeatureVariable(BaseModel):
    description: str | None
    enum: list[str] | None
    fallbackPref: str | None
    type: FeatureVariableType | None
    setPref: str | None


class FeatureSchema(BaseModel):
    uri: str | None
    path: str | None


class Feature(BaseModel):
    applicationSlug: str
    description: str | None
    exposureDescription: Literal[False] | str | None
    isEarlyStartup: bool | None
    slug: str
    variables: dict[str, FeatureVariable] | None
    schema_paths: FeatureSchema | None = Field(alias="schema")

    def load_remote_jsonschema(self):
        if self.schema_paths:
            schema_path = os.path.join(
                settings.FEATURE_SCHEMAS_PATH,
                self.schema_paths.path,
            )

            with open(schema_path) as schema_file:
                schema_data = schema_file.read()
                try:
                    return json.dumps(json.loads(schema_data), indent=2)
                except json.JSONDecodeError:
                    return None

    def generate_jsonschema(self):
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

        if self.variables:
            for variable_slug, variable in self.variables.items():
                variable_schema = {
                    "description": variable.description,
                }

                if variable.type in FEATURE_SCHEMA_TYPES:
                    variable_schema["type"] = FEATURE_SCHEMA_TYPES[variable.type]

                if variable.enum:
                    python_type = FEATURE_PYTHON_TYPES[variable.type]
                    variable_schema["enum"] = [python_type(e) for e in variable.enum]

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
                    for feature_slug in application_data:
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
