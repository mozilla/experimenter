import json
from urllib.parse import urlparse

import pytest
import requests
from nimbus.pages.browser import Browser
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.pages.remote_settings.dashboard import Dashboard
from nimbus.pages.remote_settings.login import Login


def load_data():
    apps = []
    data = requests.post(
        "https://nginx/api/v5/graphql",
        json={
            "operationName": "getConfig",
            "variables": {},
            "query": "\nquery getConfig {\n  nimbusConfig "
            "{\n    targetingConfigs {\n      "
            "label\n      value\n      applicationValues\n    "
            "}\n  }\n}\n",
        },
        verify=False,
    ).json()
    for item in data["data"]["nimbusConfig"]["targetingConfigs"]:
        if "DESKTOP" in item["applicationValues"]:
            apps.append(item["value"])
    return apps


@pytest.fixture(params=load_data())
def app_data(request):
    return request.param


@pytest.mark.run_per_app
def test_create_new_experiment_approve_remote_settings(
    selenium,
    base_url,
    kinto_url,
    kinto_review_url,
    experiment_url,
    default_data,
    create_experiment,
):
    create_experiment(selenium).launch_and_approve()

    Login(selenium, kinto_url).open().login()
    Dashboard(selenium, kinto_review_url).open().approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()


@pytest.mark.run_once
def test_create_new_experiment_reject_remote_settings(
    selenium,
    kinto_url,
    kinto_review_url,
    experiment_url,
    create_experiment,
):
    create_experiment(selenium).launch_and_approve()

    Login(selenium, kinto_url).open().login()
    Dashboard(selenium, kinto_review_url).open().reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.run_once
def test_create_new_experiment_timeout_remote_settings(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.launch_and_approve()
    summary.wait_for_timeout_alert()


@pytest.mark.run_once
def test_end_experiment_and_approve_end(
    selenium,
    kinto_url,
    kinto_review_url,
    experiment_url,
    create_experiment,
):
    create_experiment(selenium).launch_and_approve()

    Login(selenium, kinto_url).open().login()
    Dashboard(selenium, kinto_review_url).open().approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    Dashboard(selenium, kinto_review_url).open().approve()

    SummaryPage(selenium, experiment_url).open().wait_for_complete_status()


@pytest.mark.run_once
def test_end_experiment_and_reject_end(
    selenium,
    kinto_url,
    kinto_review_url,
    experiment_url,
    create_experiment,
):
    create_experiment(selenium).launch_and_approve()

    Login(selenium, kinto_url).open().login()
    Dashboard(selenium, kinto_review_url).open().approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    Dashboard(selenium, kinto_review_url).open().reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.run_parallel
def test_check_targeting(
    selenium,
    base_url,
    default_data,
    create_experiment,
    slugify,
    app_data,
    json_url
):
    default_data.audience.targeting = app_data
    default_data.public_name = default_data.public_name.replace("-", "", 1)
    create_experiment(selenium).launch_to_preview()
    json_url = json_url(base_url, default_data.public_name)
    # Get experiment JSON and parse
    experiment_json = requests.get(f"{json_url}", verify=False).json()
    experiment_json = {"experiment": experiment_json}
    targeting = experiment_json["experiment"]["targeting"]
    experiment_json = json.dumps(experiment_json)
    # Inject filter expression
    selenium.get("about:blank")
    with open("nimbus/utils/filter_expression.js") as js:
        script = Browser.execute_script(
            selenium,
            targeting,
            experiment_json,
            script=js.read(),
            context="chrome",
        )
    assert script is not None, "Invalid Targeting, or bad recipe"
