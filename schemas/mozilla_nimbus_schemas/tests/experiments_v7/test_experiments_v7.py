import importlib.resources
import json
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

from mozilla_nimbus_schemas.experiments_v7 import (
    V7DesktopNimbusExperiment,
    V7SdkNimbusExperiment,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "experiments_v7"
PACKAGE_DIR = importlib.resources.files("mozilla_nimbus_schemas")
SCHEMAS_DIR = PACKAGE_DIR / "schemas"


@pytest.fixture
@cache
def v7_desktop_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("V7DesktopNimbusExperiment.schema.json")


@pytest.fixture
@cache
def v7_sdk_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("V7SdkNimbusExperiment.schema.json")


def load_schema(name: str) -> Validator:
    with SCHEMAS_DIR.joinpath(name).open() as f:
        schema = json.load(f)

    validator = validator_for(schema)
    validator.check_schema(schema)

    return validator(schema, format_checker=validator.FORMAT_CHECKER)


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.joinpath("desktop").iterdir())
def test_v7_desktop_experiment_fixtures_are_valid(
    experiment_file, v7_desktop_nimbus_experiment_schema_validator
):
    """Validate all v7 desktop experiment fixtures."""
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)

    V7DesktopNimbusExperiment.model_validate(experiment_json)
    v7_desktop_nimbus_experiment_schema_validator.validate(experiment_json)


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.joinpath("sdk").iterdir())
def test_v7_sdk_experiment_fixtures_are_valid(
    experiment_file, v7_sdk_nimbus_experiment_schema_validator
):
    """Validate all v7 SDK experiment fixtures."""
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)

    V7SdkNimbusExperiment.model_validate(experiment_json)
    v7_sdk_nimbus_experiment_schema_validator.validate(experiment_json)


def test_v7_desktop_nimbus_experiment_with_fxlabs_opt_in_is_not_rollout(
    v7_desktop_nimbus_experiment_schema_validator,
):
    experiment_json = _v7_desktop_nimbus_experiment(isRollout=False)
    experiment_json.update(
        {
            "isFirefoxLabsOptIn": True,
            "firefoxLabsTitle": "test-title",
            "firefoxLabsDescription": "test-desc",
            "firefoxLabsDescriptionLinks": None,
            "firefoxLabsGroup": "test-group",
        }
    )
    V7DesktopNimbusExperiment.model_validate(experiment_json)
    v7_desktop_nimbus_experiment_schema_validator.validate(experiment_json)


def _v7_desktop_nimbus_experiment(isRollout: bool) -> dict[str, Any]:
    return {
        "appId": "firefox-desktop",
        "appName": "firefox_desktop",
        "application": "firefox-desktop",
        "arguments": {},
        "branches": [
            {
                "features": [
                    {"featureId": "pocketNewtab", "value": {"enabled": "true"}},
                    {"featureId": "upgradeDialog", "value": {"enabled": False}},
                ],
                "ratio": 1,
                "slug": "control",
            },
            {
                "features": [
                    {
                        "featureId": "pocketNewtab",
                        "value": {
                            "enabled": True,
                            "compactLayout": True,
                            "lastCardMessageEnabled": True,
                            "loadMore": True,
                            "newFooterSection": True,
                        },
                    },
                    {"featureId": "upgradeDialog", "value": {"enabled": True}},
                ],
                "ratio": 1,
                "slug": "treatment",
            },
        ],
        "bucketConfig": {
            "count": 10000,
            "namespace": "firefox-desktop-multifeature-test-v7",
            "randomizationUnit": "nimbus_id",
            "start": 0,
            "total": 10000,
        },
        "channel": "nightly",
        "endDate": None,
        "featureIds": ["upgradeDialog", "pocketNewtab"],
        "id": "mr2-upgrade-spotlight-holdback-v7",
        "isEnrollmentPaused": False,
        "outcomes": [],
        "probeSets": [],
        "proposedDuration": 63,
        "proposedEnrollment": 7,
        "referenceBranch": "control",
        "schemaVersion": "2.0",
        "slug": "firefox-desktop-multifeature-test-v7",
        "startDate": "2023-12-01",
        "targeting": "true",
        "userFacingDescription": "Test data for a localized experiment",
        "userFacingName": "MR2 Upgrade Spotlight Holdback V7",
        "isRollout": bool(isRollout),
    }
