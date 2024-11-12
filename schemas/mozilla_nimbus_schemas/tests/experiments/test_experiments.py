import importlib.resources
import json
from functools import cache
from pathlib import Path
from typing import Any, Protocol

import jsonschema
import pydantic
import pytest
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

from mozilla_nimbus_schemas.experiments import (
    DesktopAllVersionsNimbusExperiment,
    DesktopNimbusExperiment,
    SdkNimbusExperiment,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "experiments"
PACKAGE_DIR = importlib.resources.files("mozilla_nimbus_schemas")
SCHEMAS_DIR = PACKAGE_DIR / "schemas"


@pytest.fixture
@cache
def desktop_all_versions_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("DesktopAllVersionsNimbusExperiment.schema.json")


@pytest.fixture
@cache
def desktop_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("DesktopNimbusExperiment.schema.json")


@pytest.fixture
@cache
def sdk_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("SdkNimbusExperiment.schema.json")


class DesktopExperimentValidator(Protocol):
    def __call__(
        self,
        experiment_json: dict[str, Any],
        *,
        valid: bool = True,
        valid_all_versions: bool = True,
    ): ...


@pytest.fixture
def validate_desktop_experiment(
    desktop_nimbus_experiment_schema_validator,
    desktop_all_versions_nimbus_experiment_schema_validator,
) -> DesktopExperimentValidator:
    def _validate(
        experiment_json: dict[str, Any],
        *,
        valid: bool = True,
        valid_all_versions: bool = True,
    ):
        assert not (not valid and valid_all_versions), "valid_all_versions implies valid"

        if valid:
            DesktopNimbusExperiment.model_validate(experiment_json)
            desktop_nimbus_experiment_schema_validator.validate(experiment_json)
        else:
            with pytest.raises(pydantic.ValidationError):
                DesktopNimbusExperiment.model_validate(experiment_json)

            with pytest.raises(jsonschema.ValidationError):
                desktop_nimbus_experiment_schema_validator.validate(experiment_json)

        if valid_all_versions:
            DesktopAllVersionsNimbusExperiment.model_validate(experiment_json)
            desktop_all_versions_nimbus_experiment_schema_validator.validate(
                experiment_json
            )
        else:
            with pytest.raises(pydantic.ValidationError):
                DesktopAllVersionsNimbusExperiment.model_validate(experiment_json)

            with pytest.raises(jsonschema.ValidationError):
                desktop_all_versions_nimbus_experiment_schema_validator.validate(
                    experiment_json
                )

    return _validate


def load_schema(name: str) -> Validator:
    with SCHEMAS_DIR.joinpath(name).open() as f:
        schema = json.load(f)

    validator = validator_for(schema)
    validator.check_schema(schema)

    return validator(schema)


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.joinpath("desktop").iterdir())
def test_desktop_experiment_fixtures_are_valid(
    experiment_file,
    validate_desktop_experiment,
):
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)

    validate_desktop_experiment(experiment_json)

    for branch in experiment_json["branches"]:
        del branch["feature"]

    # Assert that this no longer passes with the strict schema, but passes with the
    # regular schema.
    validate_desktop_experiment(experiment_json, valid_all_versions=False)


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.joinpath("sdk").iterdir())
def test_sdk_experiment_fixtures_are_valid(
    experiment_file, sdk_nimbus_experiment_schema_validator
):
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)

    SdkNimbusExperiment.model_validate(experiment_json)
    sdk_nimbus_experiment_schema_validator.validate(experiment_json)


def test_desktop_nimbus_expirement_with_fxlabs_opt_in_is_not_rollout(
    validate_desktop_experiment,
):
    experiment_json = _desktop_nimbus_experiment_with_fxlabs_opt_in(isRollout=False)
    validate_desktop_experiment(experiment_json)


def test_desktop_nimbus_experiment_with_fxlabs_opt_in_is_rollout(
    validate_desktop_experiment,
):
    experiment_json = _desktop_nimbus_experiment_with_fxlabs_opt_in(isRollout=True)
    validate_desktop_experiment(experiment_json)


def test_desktop_nimbus_experiment_without_fxlabs_opt_in(validate_desktop_experiment):
    experiment_json = _desktop_nimbus_experiment_without_fxlabs_opt_in()
    validate_desktop_experiment(experiment_json)


def test_desktop_nimbus_experiment_with_fxlabs_opt_in_but_missing_required_fields(
    validate_desktop_experiment,
    desktop_all_versions_nimbus_experiment_schema_validator,
):
    experiment_json = (
        _desktop_nimbus_experiment_with_fxlabs_opt_in_missing_required_fields()
    )
    validate_desktop_experiment(experiment_json, valid=False, valid_all_versions=False)

    assert not desktop_all_versions_nimbus_experiment_schema_validator.is_valid(
        experiment_json
    )

    errors = list(
        desktop_all_versions_nimbus_experiment_schema_validator.iter_errors(
            experiment_json
        )
    )
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
                    "featureId": "this-is-included-for-desktop-pre-95-support",
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
                    "featureId": "this-is-included-for-desktop-pre-95-support",
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
