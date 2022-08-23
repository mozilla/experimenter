import time
from urllib.parse import urljoin

import pytest
import requests
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers


@pytest.mark.run_once
@pytest.mark.nightly_only
@pytest.mark.xdist_group(name="group1")
def test_check_telemetry_enrollment_unenrollment(
    base_url,
    selenium,
    kinto_client,
    slugify,
    experiment_name,
    create_desktop_experiment,
    trigger_experiment_loader,
):
    requests.delete("http://ping-server:5000/pings")
    targeting = helpers.load_targeting_configs()[0]
    experiment_slug = str(slugify(experiment_name))
    create_desktop_experiment(
        experiment_slug,
        "desktop",
        targeting,
        public_description="Some sort of words",
        risk_revenue=False,
        risk_partner_related=False,
        risk_brand=False,
        feature_config=1,
        reference_branch={
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureEnabled": True,
            "featureValue": "{}",
        },
        treatement_branch=[
            {
                "description": "treatment branch",
                "name": "Branch 2",
                "ratio": 50,
                "featureEnabled": False,
                "featureValue": "",
            }
        ],
        population_percent="100",
        total_enrolled_clients=55,
    )
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_live_status()

    # Ping the server twice as it sleeps sometimes
    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    # Check their was a telemetry event for the enrollment
    control = True
    timeout = time.time() + 60 * 5
    while control or time.time() < timeout:
        telemetry = requests.get("http://ping-server:5000/pings").json()
        for item in reversed(telemetry):
            if "events" in item["payload"]:
                if "parent" in item["payload"]["events"]:
                    for events in item["payload"]["events"]["parent"]:
                        try:
                            assert "normandy" in events
                            assert "enroll" in events
                            assert "nimbus_experiment" in events
                            assert experiment_slug in events
                        except AssertionError:
                            continue
                        else:
                            control = False
                            break
            else:
                continue
        # If there are no pings we have to wait
        else:
            trigger_experiment_loader()
            time.sleep(15)
    else:
        if control is not False:
            assert False, "Experiment enrollment was never seen in ping Data"

    # check experiment exists, this means it is enrolled
    for item in requests.get("http://ping-server:5000/pings").json():
        if "experiments" in item["environment"]:
            for key in item["environment"]["experiments"]:
                assert experiment_slug in key

    # unenroll
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_complete_status()

    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    control = True
    timeout = time.time() + 60 * 5
    while control or time.time() < timeout:
        telemetry = requests.get("http://ping-server:5000/pings").json()
        for item in reversed(telemetry):
            if "events" in item["payload"]:
                if "parent" in item["payload"]["events"]:
                    for events in item["payload"]["events"]["parent"]:
                        try:
                            assert "normandy" in events
                            assert "unenroll" in events
                            assert "nimbus_experiment" in events
                            assert experiment_slug in events
                        except AssertionError:
                            continue
                        else:
                            control = False
                            break
            else:
                continue
        # If there are no pings we have to wait
        else:
            trigger_experiment_loader()
            time.sleep(15)
    else:
        if control is not False:
            assert False, "Experiment unenrollment was never seen in Ping Data"
