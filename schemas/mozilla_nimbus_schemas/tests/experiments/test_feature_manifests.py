from pathlib import Path
from typing import Any

import pydantic
import pytest
import yaml

from mozilla_nimbus_schemas.experiments.feature_manifests import (
    DesktopFeatureManifest,
    DesktopFeatureVariable,
    SdkFeatureManifest,
    SdkFeatureVariable,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "feature_manifests"


@pytest.mark.parametrize("manifest_file", FIXTURE_DIR.joinpath("desktop").iterdir())
def test_desktop_manifest_fixtures_are_valid(manifest_file):
    with manifest_file.open() as f:
        contents = yaml.safe_load(f)

    DesktopFeatureManifest.model_validate(contents)


@pytest.mark.parametrize("manifest_file", FIXTURE_DIR.joinpath("sdk").iterdir())
def test_sdk_manifest_fixtures_are_valid(manifest_file):
    with manifest_file.open() as f:
        contents = yaml.safe_load(f)

    SdkFeatureManifest.model_validate(contents)


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
    "model_json,expected_pydantic_error",
    [
        (
            {
                "description": "invalid enum (string options for int type)",
                "type": "int",
                "enum": ["hello"],
            },
            "only string enums are supported",
        ),
        (
            {
                "description": "invalid enum (int options for string type)",
                "type": "string",
                "enum": [1],
            },
            "Input should be a valid string",
        ),
    ],
)
def test_sdk_feature_variable_invalid_enum_type_mismatch(
    model_json,
    expected_pydantic_error,
):
    with pytest.raises(pydantic.ValidationError, match=expected_pydantic_error):
        SdkFeatureVariable.model_validate(model_json)


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
def test_desktop_feature_variable_invalid_enum_types(model_json):
    with pytest.raises(pydantic.ValidationError):
        DesktopFeatureVariable.model_validate(model_json)


@pytest.mark.parametrize(
    "model_json",
    [
        {
            "description": "invalid enum (string options for int type)",
            "type": "int",
            "enum": ["hello"],
        },
        {
            "description": "invalid enum (int options for string type)",
            "type": "string",
            "enum": [1],
        },
    ],
)
def test_desktop_feature_variable_invalid_enum_type_mismatch(model_json):
    with pytest.raises(
        pydantic.ValidationError, match="enum values do not match variable type"
    ):
        DesktopFeatureVariable.model_validate(model_json)


def test_desktop_feature_variable_invalid_fallback_pref_set_pref_mutually_exclusive():
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
