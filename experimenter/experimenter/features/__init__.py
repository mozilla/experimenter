import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from django.conf import settings
from mozilla_nimbus_schemas.experimenter_apis.experiments.feature_manifests import (
    DesktopFeature,
    DesktopFeatureManifest,
    FeatureVariableType,
    SdkFeature,
    SdkFeatureManifest,
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
    model: SdkFeature | DesktopFeature
    version: Version | None = None

    @classmethod
    def load_remote_jsonschema(cls, application_slug: str, feature_model: DesktopFeature):
        if feature_model.json_schema is not None:
            schema_path = (
                settings.FEATURE_MANIFESTS_PATH
                / application_slug
                / "schemas"
                / feature_model.json_schema.path
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

    @property
    def has_remote_schema(self):
        return (
            isinstance(self.model, DesktopFeature) and self.model.json_schema is not None
        )

    def get_jsonschema(self):
        if self.has_remote_schema:
            return self.load_remote_jsonschema(self.application_slug, self.model)

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

            if application.slug == NimbusConstants.Application.DESKTOP:
                manifest_cls = DesktopFeatureManifest
            else:
                manifest_cls = SdkFeatureManifest

            manifest = manifest_cls.parse_obj(application_data)

            for feature_slug, feature_model in manifest.root.items():
                yield Feature(
                    slug=feature_slug,
                    application_slug=application.slug,
                    model=feature_model,
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
