import importlib.resources
import json
from functools import cache
from pathlib import Path
from typing import Any

import pydantic
import pytest
import yaml
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

from mozilla_nimbus_schemas.experiments.feature_manifests import (
    DesktopFeatureManifest,
    DesktopFeatureVariable,
    SdkFeatureManifest,
    SdkFeatureVariable,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "feature_manifests"

PACKAGE_DIR = importlib.resources.files("mozilla_nimbus_schemas")
SCHEMAS_DIR = PACKAGE_DIR / "schemas"


def load_schema(name: str) -> Validator:
    with SCHEMAS_DIR.joinpath(name).open() as f:
        schema = json.load(f)

    validator = validator_for(schema)
    validator.check_schema(schema)

    return validator(schema)


@pytest.fixture
@cache
def desktop_feature_schema_validator() -> Validator:
    return load_schema("DesktopFeature.schema.json")


@pytest.fixture
@cache
def desktop_feature_manifest_schema_validator() -> Validator:
    return load_schema("DesktopFeatureManifest.schema.json")


@pytest.fixture
@cache
def sdk_feature_manifest_schema_validator() -> Validator:
    return load_schema("SdkFeatureManifest.schema.json")


@pytest.mark.parametrize("manifest_file", FIXTURE_DIR.joinpath("desktop").iterdir())
def test_desktop_manifest_fixtures_are_valid(
    manifest_file, desktop_feature_manifest_schema_validator
):
    with manifest_file.open() as f:
        contents = yaml.safe_load(f)

    DesktopFeatureManifest.model_validate(contents)

    assert desktop_feature_manifest_schema_validator.is_valid(contents)


@pytest.mark.parametrize("manifest_file", FIXTURE_DIR.joinpath("sdk").iterdir())
def test_sdk_manifest_fixtures_are_valid(
    manifest_file, sdk_feature_manifest_schema_validator
):
    with manifest_file.open() as f:
        contents = yaml.safe_load(f)

    SdkFeatureManifest.model_validate(contents)

    assert sdk_feature_manifest_schema_validator.is_valid(contents)


def test_desktop_feature_exposure_description_conditionally_required(
    desktop_feature_schema_validator,
):
    assert desktop_feature_schema_validator.is_valid(
        {
            "owner": "owner@example.com",
            "description": "placeholder",
            "hasExposure": False,
            "variables": {},
        }
    )

    errors = list(
        desktop_feature_schema_validator.iter_errors(
            {
                "owner": "owner@example.com",
                "description": "placeholder",
                "hasExposure": True,
                "variables": {},
            }
        )
    )

    assert [e.message for e in errors] == ["'exposureDescription' is a required property"]
    assert tuple(errors[0].path) == ()


def test_sdk_feature_manifest_feature_exposure_description_conditionally_required(
    sdk_feature_manifest_schema_validator,
):
    manifest = {
        "feature": {
            "description": "placeholder",
            "hasExposure": False,
            "variables": {},
        },
    }
    assert sdk_feature_manifest_schema_validator.is_valid(manifest)

    manifest["feature"]["hasExposure"] = True

    errors = list(sdk_feature_manifest_schema_validator.iter_errors(manifest))

    assert [e.message for e in errors] == ["'exposureDescription' is a required property"]
    assert tuple(errors[0].path) == ("feature",)


def test_sdk_feature_variable_valid_enum():
    SdkFeatureVariable.model_validate(
        {"description": "valid enum", "type": "string", "enum": ["hello", "world"]},
    )


@pytest.mark.parametrize(
    "model_json",
    [
        {
            "description": "invalid enum (int not supported)",
            "type": "int",
            "enum": [1, 2, 3],
        },
        {
            "description": "invalid enum (boolean not supported)",
            "type": "boolean",
            "enum": [True],
        },
        {
            "description": "invalid enum (json not supported)",
            "type": "json",
            "enum": [{}, {}],
        },
    ],
)
def test_sdk_feature_variable_invalid_enum_unsupported_type(model_json):
    with pytest.raises(pydantic.ValidationError, match="Input should be a valid string"):
        SdkFeatureVariable.model_validate(model_json)


@pytest.mark.parametrize(
    "model_json,expected_pydantic_error,expected_jsonschema_error,expected_jsonschema_error_path",
    [
        (
            {
                "description": "invalid enum (string options for int type)",
                "type": "int",
                "enum": ["hello"],
            },
            "only string enums are supported",
            "'string' was expected",
            ("feature", "variables", "variable", "type"),
        ),
        (
            {
                "description": "invalid enum (int options for string type)",
                "type": "string",
                "enum": [1],
            },
            "Input should be a valid string",
            "1 is not of type 'string'",
            ("feature", "variables", "variable", "enum", 0),
        ),
    ],
)
def test_sdk_feature_variable_invalid_enum_type_mismatch(
    model_json,
    expected_pydantic_error,
    expected_jsonschema_error,
    expected_jsonschema_error_path,
    sdk_feature_manifest_schema_validator,
):
    with pytest.raises(pydantic.ValidationError, match=expected_pydantic_error):
        SdkFeatureVariable.model_validate(model_json)

    manifest = {
        "feature": {
            "description": "description",
            "hasExposure": False,
            "variables": {
                "variable": model_json,
            },
        }
    }

    errors = list(sdk_feature_manifest_schema_validator.iter_errors(manifest))
    assert [e.message for e in errors] == [expected_jsonschema_error]
    assert tuple(errors[0].path) == expected_jsonschema_error_path


@pytest.mark.parametrize(
    "model_json",
    [
        {
            "description": "valid enum (string)",
            "type": "string",
            "enum": ["foo", "bar"],
        },
        {
            "description": "valid enum (int)",
            "type": "int",
            "enum": [1, 2, 10],
        },
    ],
)
def test_desktop_feature_variable_valid_enum(model_json):
    DesktopFeatureVariable.model_validate(model_json)


def _desktop_feature_with_variable(variable: dict[str, Any]) -> dict[str, Any]:
    return {
        "description": "description",
        "hasExposure": False,
        "owner": "placeholder@example.com",
        "variables": {
            "variable": variable,
        },
    }


@pytest.mark.parametrize(
    "model_json",
    [
        {
            "description": "invalid enum (boolean)",
            "type": "boolean",
            "enum": [True],
        },
        {
            "description": "invalid enum (json)",
            "type": "json",
            "enum": [{}],
        },
    ],
)
def test_desktop_feature_variable_invalid_enum_types(
    model_json, desktop_feature_schema_validator
):
    with pytest.raises(pydantic.ValidationError):
        DesktopFeatureVariable.model_validate(model_json)

    errors = list(
        desktop_feature_schema_validator.iter_errors(
            _desktop_feature_with_variable(model_json)
        )
    )

    assert [e.message for e in errors] == [
        "None was expected",
        f"{str(model_json['enum'])} is not valid under any of the given schemas",
    ]

    assert tuple(errors[0].path) == ("variables", "variable", "enum")


@pytest.mark.parametrize(
    "model_json,expected_error",
    [
        (
            {
                "description": "invalid enum (string options for int type)",
                "type": "int",
                "enum": ["hello"],
            },
            "'hello' is not of type 'integer'",
        ),
        (
            {
                "description": "invalid enum (int options for string type)",
                "type": "string",
                "enum": [1],
            },
            "1 is not of type 'string'",
        ),
    ],
)
def test_desktop_feature_variable_invalid_enum_type_mismatch(
    model_json, expected_error, desktop_feature_schema_validator
):
    with pytest.raises(
        pydantic.ValidationError, match="enum values do not match variable type"
    ):
        DesktopFeatureVariable.model_validate(model_json)

    errors = list(
        desktop_feature_schema_validator.iter_errors(
            _desktop_feature_with_variable(model_json)
        )
    )

    assert [e.message for e in errors] == [expected_error]
    assert tuple(errors[0].path) == ("variables", "variable", "enum", 0)


def test_desktop_feature_variable_invalid_fallback_pref_set_pref_mutually_exclusive(
    desktop_feature_schema_validator,
):
    model_json = {
        "description": "invalid variable (fallbackPref and setPref mutually exclusive)",
        "type": "string",
        "setPref": {
            "branch": "user",
            "pref": "foo.bar",
        },
        "fallbackPref": "baz.qux",
    }

    with pytest.raises(
        pydantic.ValidationError,
        match="fallback_pref and set_pref are mutually exclusive",
    ):
        DesktopFeatureVariable.model_validate(model_json)

    errors = list(
        desktop_feature_schema_validator.iter_errors(
            _desktop_feature_with_variable(model_json)
        )
    )

    assert [e.message for e in errors] == ["None was expected", "None was expected"]
    assert tuple(errors[0].path) == ("variables", "variable", "setPref")
    assert tuple(errors[1].path) == ("variables", "variable", "fallbackPref")
