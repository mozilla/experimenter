from json import load
from urllib.parse import urlparse

import pytest
import requests
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
            "query": "\nquery getConfig {\n  nimbusConfig {\n    targetingConfigs {\n      label\n      value\n      applicationValues\n    }\n  }\n}\n",
        },
        verify=False,
        ).json()
    # print(data["data"]["nimbusConfig"]["targetingConfigs"][1]["applicationValues"])
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


def test_create_new_experiment_approve_check_targeting(
    selenium,
    base_url,
    kinto_url,
    kinto_review_url,
    experiment_url,
    default_data,
    create_experiment,
    slugify,
    app_data
    
):
    print(app_data)
    default_data.audience.targeting = app_data
    # default_data.audience.locale = "English (Canadian)"
    # default_data.audience.countries = "Canada"
    experiment = create_experiment(selenium).launch_to_preview()

    # Login(selenium, kinto_url).open().login()
    # Dashboard(selenium, kinto_review_url).open().approve()
    # SummaryPage(selenium, experiment_url).open().wait_for_live_status()
    title = default_data.public_name
    base_url = urlparse(base_url)
    json_url = f"https://{base_url.netloc}/api/v6/experiments/{slugify(title)}"
    # Get experiment JSON and parse
    experiment_json = requests.get(f"{json_url}", verify=False).json()
    targeting = experiment_json["targeting"]
    # expression = []
    # environment = []
    # for item in targetting.split("&&"):
    #     if "locale" in item or "region" in item:
    #         environment.append(item)
    #     else:
    #         expression.append(item)
    # if environment is False:
    #     environment = "en-US"
    # expression = "&&".join(expression)
    # environment = "&&".join(environment)
    # Inject filter expression
    selenium.get("about:blank")
    with open("nimbus/utils/filter_expression.js") as js:
        with selenium.context(selenium.CONTEXT_CHROME):
            script = selenium.execute_script(js.read(), targeting, experiment_json)
    assert script is not None
