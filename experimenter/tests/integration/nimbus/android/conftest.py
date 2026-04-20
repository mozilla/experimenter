import os
import time
from pathlib import Path

import pytest
import requests

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.utils import helpers

FENIX_APP = BaseExperimentApplications.FIREFOX_FENIX.value
RECIPE_POLL_TIMEOUT = 60


@pytest.fixture(name="fenix_channel")
def fixture_fenix_channel():
    value = os.environ.get("FENIX_CHANNEL")
    if not value:
        pytest.skip("FENIX_CHANNEL is not set")
    return value


@pytest.fixture(name="fenix_apk_path")
def fixture_fenix_apk_path():
    value = os.environ.get("FENIX_APK_PATH")
    if not value or not Path(value).exists():
        pytest.skip(f"FENIX_APK_PATH not set or missing: {value!r}")
    return value


@pytest.fixture
def experiment_slug(fenix_channel):
    return f"fenix-{fenix_channel}-integration-test"


def wait_for_recipe(slug):
    base_url = os.environ.get("INTEGRATION_TEST_NGINX_URL", "https://nginx")
    url = f"{base_url}/api/v6/experiments/{slug}/"
    deadline = time.time() + RECIPE_POLL_TIMEOUT
    last_error = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, verify=False, timeout=5)
            if resp.status_code == 200:
                recipe = resp.json()
                if recipe.get("slug") == slug and recipe.get("bucketConfig"):
                    return recipe
                last_error = (
                    f"recipe missing bucketConfig: {recipe.get('bucketConfig')!r}"
                )
            else:
                last_error = f"HTTP {resp.status_code}"
        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc)
        time.sleep(1)
    pytest.fail(f"Timed out waiting for recipe at {url} ({last_error})")


@pytest.fixture
def create_fenix_experiment(application_feature_ids):
    def _create_fenix_experiment(slug, channel):
        feature_id = application_feature_ids[FENIX_APP]
        helpers.create_experiment(
            slug,
            FENIX_APP,
            data={
                "feature_config_ids": [int(feature_id)],
                "reference_branch": {
                    "name": "control",
                    "description": "control branch",
                },
                "population_percent": "100",
                "total_enrolled_clients": "1000000",
                "channel": channel,
                "firefox_min_version": "",
            },
            targeting="no_targeting",
        )
        helpers.launch_to_preview(slug)
        return wait_for_recipe(slug)

    return _create_fenix_experiment
