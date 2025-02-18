import importlib.resources
import json
from functools import cache
from pathlib import Path

import pytest
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

from mozilla_nimbus_schemas.experimenter_apis.experiments_v7 import NimbusExperimentV7

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "experiments_v7"
PACKAGE_DIR = importlib.resources.files("mozilla_nimbus_schemas")
SCHEMAS_DIR = PACKAGE_DIR / "schemas"


@pytest.fixture
@cache
def v7_nimbus_experiment_schema_validator() -> Validator:
    return load_schema("NimbusExperimentV7.schema.json")


def load_schema(name: str) -> Validator:
    with SCHEMAS_DIR.joinpath(name).open() as f:
        schema = json.load(f)

    validator = validator_for(schema)
    validator.check_schema(schema)

    return validator(schema, format_checker=validator.FORMAT_CHECKER)


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.iterdir())
def test_v7_experiment_fixtures_are_valid(
    experiment_file, v7_nimbus_experiment_schema_validator
):
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)

    NimbusExperimentV7.model_validate(experiment_json)
    v7_nimbus_experiment_schema_validator.validate(experiment_json)
