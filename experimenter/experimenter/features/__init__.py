import json
import os
from dataclasses import dataclass
from typing import Union

import yaml
from django.conf import settings
from django.core.checks import Error, register
from mozilla_nimbus_schemas.experiments.feature_manifests import (
    FeatureManifest,
    FeatureVariableType,
    FeatureWithExposure,
    FeatureWithoutExposure,
)

from experimenter.experiments.constants import NimbusConstants

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


@dataclass
class Feature:
    slug: str
    application_slug: str
    model: Union[FeatureWithExposure, FeatureWithoutExposure]

    def load_remote_jsonschema(self):
        if self.model.json_schema is not None:
            schema_path = os.path.join(
                settings.FEATURE_MANIFESTS_PATH,
                self.application_slug,
                "schemas",
                self.model.json_schema.path,
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

        for variable_slug, variable in self.model.variables.items():
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
        if self.model.json_schema is not None:
            return self.load_remote_jsonschema()
        return self.generate_jsonschema()


class Features:
    _features = None

    @classmethod
    def _load_features(cls):
        features = []

        for application in NimbusConstants.APPLICATION_CONFIGS.values():
            application_yaml_path = os.path.join(
                settings.FEATURE_MANIFESTS_PATH, application.slug, "experimenter.yaml"
            )

            if os.path.exists(application_yaml_path):
                with open(application_yaml_path) as application_yaml_file:
                    application_data = yaml.safe_load(application_yaml_file)
                    manifest = FeatureManifest.parse_obj(application_data)

                    for feature_slug, feature_model in manifest.__root__.items():
                        features.append(
                            Feature(
                                slug=feature_slug,
                                application_slug=application.slug,
                                model=feature_model.__root__,
                            )
                        )

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
        return [f for f in cls.all() if f.application_slug == application]


@register()
def check_features(app_configs, **kwargs):
    errors = []

    try:
        Features.all()
    except Exception as e:
        errors.append(Error(f"Error loading feature data {e}"))
    return errors
