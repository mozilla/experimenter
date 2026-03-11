import json
import logging
import time
from pathlib import Path

import pytest
import requests

from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers


@pytest.fixture
def experiment_slug(application):
    return f"firefox-{application.lower()}-integration-test"


def test_create_mobile_experiment_for_integration_test(
    selenium, experiment_url, kinto_client, experiment_slug, application
):
    """Create a mobile experiment for device integration tests"""
    apps = ["ios", "fenix"]

    if str(application) not in apps:
        pytest.skip()
    feature_config_id = helpers.get_feature_id_as_string("messaging", application)
    helpers.create_experiment(
        experiment_slug,
        application,
        {
            "feature_config_ids": [int(feature_config_id)],
            "reference_branch": {"description": "control", "name": "control"},
        },
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    path = Path.cwd()
    timeout = time.time() + 30
    while time.time() < timeout:
        try:
            recipe = requests.get(
                f"https://nginx/api/v6/experiments/{experiment_slug}/", verify=False
            ).json()
        except Exception:
            time.sleep(1)
            continue
        else:
            json_file = (
                path
                / "experimenter"
                / "tests"
                / "integration"
                / f"{str(application).lower()}_recipe.json"
            )
            json_file.write_text(json.dumps(recipe))
            logging.info(f"{str(application).lower()} recipe created at {json_file}")
            break
