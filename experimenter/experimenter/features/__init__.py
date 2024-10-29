import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

import yaml
from django.conf import settings
from django.core.checks import Error, register
from mozilla_nimbus_schemas.experiments.feature_manifests import (
    FeatureManifest,
    FeatureVariableType,
    FeatureWithExposure,
    FeatureWithoutExposure,
)

from experimenter.experiments.constants import ApplicationConfig, NimbusConstants
from manifesttool.version import Version

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
    version: Optional[Version] = None

    def load_remote_jsonschema(self):
        if self.model.json_schema is not None:
            schema_path = (
                settings.FEATURE_MANIFESTS_PATH
                / self.application_slug
                / "schemas"
                / self.model.json_schema.path
            )

            with schema_path.open() as f:
                try:
                    return json.dumps(json.load(f), indent=2)
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
    _features: Optional[list[Feature]] = None

    @classmethod
    def _read_manifest(
        cls,
        application: ApplicationConfig,
        manifest_path: Path,
        version: Version = None,
    ):
        with manifest_path.open() as manifest_file:
            application_data = yaml.safe_load(manifest_file)
            manifest = FeatureManifest.parse_obj(application_data)

            for feature_slug, feature_model in manifest.__root__.items():
                yield Feature(
                    slug=feature_slug,
                    application_slug=application.slug,
                    model=feature_model.__root__,
                    version=version,
                )

    @classmethod
    def _load_features(cls):
        features = []
        version_re = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)")

        for application in NimbusConstants.APPLICATION_CONFIGS.values():
            application_dir: Path = settings.FEATURE_MANIFESTS_PATH / application.slug
            application_yaml_path = application_dir / "experimenter.yaml"

            if application_yaml_path.exists():
                features.extend(cls._read_manifest(application, application_yaml_path))

                for child in application_dir.iterdir():
                    if not child.is_dir():
                        continue

                    if m := version_re.match(child.name):
                        version = Version.from_match(m.groupdict())

                        application_yaml_path = child / "experimenter.yaml"
                        if application_yaml_path.exists():
                            features.extend(
                                cls._read_manifest(
                                    application, application_yaml_path, version
                                )
                            )

        return features

    @classmethod
    def clear_cache(cls):
        cls._features = None

    @classmethod
    def all(cls) -> list[Feature]:
        if cls._features is None:
            cls._features = cls._load_features()

        return cls._features

    @classmethod
    def by_application(cls, application) -> list[Feature]:
        return [f for f in cls.all() if f.application_slug == application]

    @classmethod
    def unversioned(cls) -> Iterable[Feature]:
        return (f for f in cls.all() if f.version is None)

    @classmethod
    def versioned(cls) -> Iterable[Feature]:
        return (f for f in cls.all() if f.version is not None)


@register()
def check_features(app_configs, **kwargs):
    errors = []

    try:
        Features.all()
    except Exception as e:
        errors.append(Error(f"Error loading feature data {e}"))
    return errors
