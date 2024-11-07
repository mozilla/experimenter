import importlib.resources
import json
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

from mozilla_nimbus_schemas.experiments import (
    DesktopNimbusExperiment,
    SdkNimbusExperiment,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "experiments"
PACKAGE_DIR = importlib.resources.files("mozilla_nimbus_schemas")
SCHEMAS_DIR = PACKAGE_DIR / "schemas"


@pytest.fixture
@cache
def desktop_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("DesktopNimbusExperiment.schema.json")


@pytest.fixture
@cache
def sdk_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("SdkNimbusExperiment.schema.json")


def load_schema(name: str) -> Validator:
    with SCHEMAS_DIR.joinpath(name).open() as f:
        schema = json.load(f)

    validator = validator_for(schema)
    validator.check_schema(schema)

    return validator(schema)


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.joinpath("desktop").iterdir())
def test_desktop_experiment_fixtures_are_valid(
    experiment_file, desktop_nimbus_experiment_schema_validator
):
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)
        print(experiment_json)
        DesktopNimbusExperiment.model_validate(experiment_json)

    desktop_nimbus_experiment_schema_validator.validate(experiment_json)


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.joinpath("sdk").iterdir())
def test_sdk_experiment_fixtures_are_valid(
    experiment_file, sdk_nimbus_experiment_schema_validator
):
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)
        print(experiment_json)
        SdkNimbusExperiment.model_validate(experiment_json)

    sdk_nimbus_experiment_schema_validator.validate(experiment_json)


def test_desktop_nimbus_expirement_with_fxlabs_opt_in_is_not_rollout(
    desktop_nimbus_experiment_schema_validator,
):
    experiment = _desktop_nimbus_experiment_with_fxlabs_opt_in(isRollout=False)

    assert desktop_nimbus_experiment_schema_validator.is_valid(experiment)


def test_desktop_nimbus_experiment_with_fxlabs_opt_in_is_rollout(
    desktop_nimbus_experiment_schema_validator,
):
    experiment = _desktop_nimbus_experiment_with_fxlabs_opt_in(isRollout=True)

    assert desktop_nimbus_experiment_schema_validator.is_valid(experiment)


def test_desktop_nimbus_experiment_without_fxlabs_opt_in(
    desktop_nimbus_experiment_schema_validator,
):
    experiment = _desktop_nimbus_experiment_without_fxlabs_opt_in()

    assert desktop_nimbus_experiment_schema_validator.is_valid(experiment)


def test_desktop_nimbus_experiment_with_fxlabs_opt_in_but_missing_required_fields(
    desktop_nimbus_experiment_schema_validator,
):
    experiment = _desktop_nimbus_experiment_with_fxlabs_opt_in_missing_required_fields()

    assert not desktop_nimbus_experiment_schema_validator.is_valid(experiment)

    errors = list(desktop_nimbus_experiment_schema_validator.iter_errors(experiment))
    error_messages = [e.message for e in errors]

    assert len(error_messages) == 4
    assert error_messages.count("'firefoxLabsTitle' is a required property") == 3
    assert error_messages.count("'firefoxLabsDescription' is a required property") == 1


def _desktop_nimbus_experiment(isRollout: bool) -> dict[str, Any]:
    return {
        "appId": "firefox-desktop",
        "appName": "firefox_desktop",
        "application": "firefox-desktop",
        "arguments": {},
        "branches": [
            {
                "feature": {
                    "featureId": "unused-feature-id-for-legacy-support",
                    "enabled": False,
                    "value": {},
                },
                "features": [
                    {"featureId": "pocketNewtab", "value": {"enabled": "true"}},
                    {"featureId": "upgradeDialog", "value": {"enabled": False}},
                ],
                "ratio": 1,
                "slug": "control",
            },
            {
                "feature": {
                    "featureId": "unused-feature-id-for-legacy-support",
                    "enabled": False,
                    "value": {},
                },
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
            "namespace": "firefox-desktop-multifeature-test",
            "randomizationUnit": "normandy_id",
            "start": 0,
            "total": 10000,
        },
        "channel": "nightly",
        "endDate": None,
        "featureIds": ["upgradeDialog", "pocketNewtab"],
        "id": "mr2-upgrade-spotlight-holdback",
        "isEnrollmentPaused": False,
        "outcomes": [],
        "probeSets": [],
        "proposedDuration": 63,
        "proposedEnrollment": 7,
        "referenceBranch": "control",
        "schemaVersion": "1.7.1",
        "slug": "firefox-desktop-multifeature-test",
        "startDate": "2021-10-26",
        "targeting": "true",
        "userFacingDescription": "Test user facing description",
        "userFacingName": "MR2 Upgrade Spotlight Holdback",
        "isRollout": bool(isRollout),
    }


def _desktop_nimbus_experiment_with_fxlabs_opt_in(*, isRollout: bool) -> dict[str, Any]:
    experiment = _desktop_nimbus_experiment(isRollout=isRollout)
    experiment.update(
        {
            "isFirefoxLabsOptIn": True,
            "firefoxLabsTitle": "test-title",
            "firefoxLabsDescription": "test-desc",
        }
    )
    experiment["branches"][0]["firefoxLabsTitle"] = "branch-one-fx-labs-title"
    experiment["branches"][1]["firefoxLabsTitle"] = "branch-two-fx-labs-title"
    return experiment


def _desktop_nimbus_experiment_with_fxlabs_opt_in_missing_required_fields() -> (
    dict[str, Any]
):
    experiment = _desktop_nimbus_experiment(isRollout=False)
    experiment.update(
        {
            "isFirefoxLabsOptIn": True,
        }
    )

    return experiment


def _desktop_nimbus_experiment_without_fxlabs_opt_in() -> dict[str, Any]:
    experiment = _desktop_nimbus_experiment(isRollout=False)
    experiment.update(
        {
            "isFirefoxLabsOptIn": False,
        }
    )

    return experiment
