import json
import os
import time

import pytest
import requests
from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.utils import helpers

IOS_APP = BaseExperimentApplications.FIREFOX_IOS.value
RECIPE_POLL_TIMEOUT = 60


def wait_for_recipe(slug):
    url = f"{os.environ.get('INTEGRATION_TEST_NGINX_URL', 'https://nginx')}/api/v6/experiments/{slug}/"
    deadline = time.time() + RECIPE_POLL_TIMEOUT
    while time.time() < deadline:
        try:
            resp = requests.get(url, verify=False, timeout=5)
            if resp.status_code == 200 and resp.json().get("bucketConfig"):
                return resp.json()
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1)
    pytest.fail(f"Timed out waiting for recipe at {url}")


@pytest.mark.ios_create_recipe
def test_create_ios_recipe(ios_channel, ios_recipe_path):
    slug = f"ios-{ios_channel}-integration-test"
    feature_id = helpers.get_feature_id_as_string("no-feature-ios", IOS_APP)
    assert feature_id
    helpers.create_experiment(
        slug,
        IOS_APP,
        data={
            "feature_config_ids": [int(feature_id)],
            "channel": ios_channel,
            "firefox_min_version": "",
        },
        targeting="no_targeting",
    )
    helpers.launch_to_preview(slug)
    ios_recipe_path.write_text(json.dumps(wait_for_recipe(slug)))
