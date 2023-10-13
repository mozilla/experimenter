from pathlib import Path

import pytest

from mozilla_nimbus_schemas.experiments import NimbusExperiment

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "experiments"


@pytest.mark.parametrize("experiment_file", FIXTURE_DIR.iterdir())
def test_experiment_fixtures_are_valid(experiment_file):
    NimbusExperiment.parse_file(experiment_file)
