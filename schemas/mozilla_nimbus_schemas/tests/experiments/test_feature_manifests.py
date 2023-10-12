from pathlib import Path

import pytest
import yaml

from mozilla_nimbus_schemas.experiments import FeatureManifest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "feature_manifests"


@pytest.mark.parametrize("manifest_file", FIXTURE_DIR.iterdir())
def test_manifest_fixtures_are_valid(manifest_file):
    with manifest_file.open() as f:
        contents = yaml.safe_load(f)

    FeatureManifest.parse_obj(contents)
