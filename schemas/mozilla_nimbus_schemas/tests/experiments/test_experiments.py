import json
from pathlib import Path

import pytest

from mozilla_nimbus_schemas.experiments import NimbusExperiment

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "experiments"


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.iterdir())
def test_experiment_fixtures_are_valid(experiment_file):
    with open(experiment_file, "r") as f:
        experiment_json = json.load(f)
        print(experiment_json)
        NimbusExperiment.model_validate(experiment_json)
