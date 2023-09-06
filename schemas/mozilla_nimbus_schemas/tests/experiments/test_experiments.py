import os

import pytest

from mozilla_nimbus_schemas.experiments import NimbusExperiment

PATH = os.path.dirname(__file__)
JSON_FILES = [
    os.path.join(PATH, "fixtures", f) for f in os.listdir(os.path.join(PATH, "fixtures"))
]


@pytest.mark.parametrize("experiment_file", JSON_FILES)
def test_experiment_fixtures_are_valid(experiment_file):
    NimbusExperiment.parse_file(experiment_file)
