import contextlib
import json
import os
import time

import pytest

from nimbus.kinto.client import KINTO_COLLECTION_WEB, KintoClient
from nimbus.utils import helpers

APPLICATION = "experimenter"
FEATURE_SLUG = "example-feature"
FEATURE_EMOJI = "\N{SNOWMAN}"
LIST_PAGE_PATH = "/nimbus/"
CIRRUS_RETRIES = 60
CIRRUS_RETRY_DELAY = 2.0


def read_title():
    html = helpers.get_page_text(LIST_PAGE_PATH)
    if "<title>" not in html:
        raise AssertionError("Experiment list page did not render a title")
    return html.split("<title>", 1)[1].split("</title>", 1)[0]


def wait_for_title_emoji():
    title = read_title()
    for _ in range(CIRRUS_RETRIES):
        if FEATURE_EMOJI in title:
            return title
        time.sleep(CIRRUS_RETRY_DELAY)
        title = read_title()
    return title


@pytest.mark.experimenter_cirrus
def test_experimenter_cirrus_serves_launched_recipe(experiment_slug):
    feature_config_id = helpers.get_feature_id_as_string(FEATURE_SLUG, APPLICATION)
    assert feature_config_id is not None, (
        f"No {FEATURE_SLUG} feature config for the {APPLICATION} application"
    )

    kinto_client = KintoClient(
        collection=KINTO_COLLECTION_WEB,
        server_url=os.getenv("INTEGRATION_TEST_KINTO_URL", "http://kinto:8888/v1"),
    )

    # CirrusMiddleware only calls Cirrus once the request user has glean prefs,
    # which GleanMiddleware creates on the first authenticated request. Reading the
    # page here both bootstraps those prefs and proves the emoji is absent before
    # the recipe is launched, so the assertion below cannot pass vacuously.
    assert FEATURE_EMOJI not in read_title()

    helpers.create_experiment(
        experiment_slug,
        APPLICATION,
        targeting="",
        is_rollout=True,
        data={
            "channel": "developer",
            "firefox_min_version": "",
            "feature_config_ids": [int(feature_config_id)],
            "reference_branch": {
                "feature_value": json.dumps(
                    {"enabled": True, "emoji": FEATURE_EMOJI}, ensure_ascii=False
                ),
            },
        },
    )

    try:
        helpers.launch_experiment(experiment_slug)
        kinto_client.approve()
        helpers.wait_for_published_recipe(experiment_slug)

        title = wait_for_title_emoji()
        assert FEATURE_EMOJI in title, (
            f"Cirrus did not apply {FEATURE_SLUG} from {experiment_slug},"
            f" list page title was {title!r}"
        )
    finally:
        with contextlib.suppress(Exception):
            helpers.end_experiment(experiment_slug)
            kinto_client.approve()
