import time
from urllib.parse import urljoin

import pytest
import requests
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers


@pytest.fixture
def firefox_options(firefox_options):
    """Set Firefox Options."""
    firefox_options.log.level = "trace"
    firefox_options.set_preference("browser.cache.disk.smart_size.enabled", False)
    firefox_options.set_preference("toolkit.telemetry.server", "http://ping-server:5000")
    firefox_options.set_preference("telemetry.fog.test.localhost_port", -1)
    firefox_options.set_preference("toolkit.telemetry.initDelay", 1)
    firefox_options.set_preference("toolkit.telemetry.minSubsessionLength", 0)
    firefox_options.set_preference("datareporting.healthreport.uploadEnabled", True)
    firefox_options.set_preference("datareporting.policy.dataSubmissionEnabled", True)
    firefox_options.set_preference("remote.prefs.recommended", False)
    firefox_options.set_preference(
        "datareporting.policy.dataSubmissionPolicyBypassNotification", False
    )
    firefox_options.set_preference("toolkit.telemetry.log.level", "Trace")
    firefox_options.set_preference("toolkit.telemetry.log.dump", True)
    firefox_options.set_preference("toolkit.telemetry.send.overrideOfficialCheck", True)
    firefox_options.set_preference("toolkit.telemetry.testing.disableFuzzingDelay", True)
    firefox_options.set_preference("nimbus.debug", True)
    firefox_options.set_preference("app.normandy.run_interval_seconds", 30)
    firefox_options.set_preference(
        "security.content.signature.root_hash",
        "5E:36:F2:14:DE:82:3F:8B:29:96:89:23:5F:03:41:AC:AF:A0:75:AF:82:CB:4C:D4:30:7C:3D:B3:43:39:2A:FE",  # noqa: E501
    )
    firefox_options.set_preference("services.settings.server", "http://kinto:8888/v1")
    firefox_options.set_preference("datareporting.healthreport.service.enabled", True)
    firefox_options.set_preference(
        "datareporting.healthreport.logging.consoleEnabled", True
    )
    firefox_options.set_preference("datareporting.healthreport.service.firstRun", True)
    firefox_options.set_preference(
        "datareporting.healthreport.documentServerURI",
        "https://www.mozilla.org/legal/privacy/firefox.html#health-report",
    )
    firefox_options.set_preference(
        "app.normandy.api_url", "https://normandy.cdn.mozilla.net/api/v1"
    )
    firefox_options.set_preference(
        "app.normandy.user_id", "7ef5ab6d-42d6-4c4e-877d-c3174438050a"
    )
    firefox_options.set_preference("messaging-system.log", "debug")
    firefox_options.set_preference("app.shield.optoutstudies.enabled", True)
    firefox_options.set_preference("toolkit.telemetry.scheduler.tickInterval", 30)
    firefox_options.set_preference("toolkit.telemetry.collectInterval", 1)
    firefox_options.set_preference("toolkit.telemetry.eventping.minimumFrequency", 30000)
    firefox_options.set_preference("toolkit.telemetry.unified", True)
    return firefox_options

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
