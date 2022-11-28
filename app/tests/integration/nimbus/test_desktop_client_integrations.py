import time
from urllib.parse import urljoin

import pytest
import requests
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
    firefox_options.set_preference("toolkit.telemetry.scheduler.tickInterval", 30)
    firefox_options.set_preference("toolkit.telemetry.collectInterval", 1)
    firefox_options.set_preference("toolkit.telemetry.eventping.minimumFrequency", 30000)
    firefox_options.set_preference("toolkit.telemetry.unified", True)
    firefox_options.set_preference("allowServerURLOverride", True)
    firefox_options.set_preference("browser.aboutConfig.showWarning", False)
    return firefox_options


@pytest.mark.nimbus_integration
@pytest.mark.xdist_group(name="group1")
def test_check_telemetry_enrollment_unenrollment(
    base_url,
    selenium,
    kinto_client,
    slugify,
    experiment_name,
    create_desktop_experiment,
    trigger_experiment_loader,
    check_ping_for_experiment,
):
    requests.delete("http://ping-server:5000/pings")
    targeting = helpers.load_targeting_configs()[0]
    experiment_slug = str(slugify(experiment_name))
    data = {
        "hypothesis": "Test Hypothesis",
        "application": "DESKTOP",
        "changelogMessage": "test updates",
        "targetingConfigSlug": targeting,
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "featureConfigId": 1,
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureEnabled": True,
            "featureValue": "{}",
        },
        "treatmentBranches": [
            {
                "description": "treatment branch",
                "name": "Branch 2",
                "ratio": 50,
                "featureEnabled": False,
                "featureValue": "",
            }
        ],
        "populationPercent": "100",
        "totalEnrolledClients": 55,
    }
    create_desktop_experiment(
        experiment_slug,
        "desktop",
        targeting,
        data,
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
    assert check_ping_for_experiment(experiment_slug)
    for item in requests.get("http://ping-server:5000/pings").json():
        if "experiments" in item["environment"]:
            for key in item["environment"]["experiments"]:
                if experiment_slug in key:
                    break
                else:
                    continue

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


@pytest.mark.nimbus_integration
@pytest.mark.xdist_group(name="group2")
def test_check_telemetry_pref_flip(
    base_url,
    selenium,
    kinto_client,
    slugify,
    experiment_name,
    create_desktop_experiment,
    experiment_default_data,
    check_ping_for_experiment,
    telemetry_event_check,
):
    _row_locator = (By.CSS_SELECTOR, "tr > td > span > span")
    _search_bar_locator = (By.ID, "about-config-search")
    wait = WebDriverWait(selenium, 60)

    def wait_function(selenium, wait_string):
        def _wait_function(selenium=selenium, wait_string=wait_string):
            try:
                selenium.get("about:config")
                search_bar = wait.until(
                    EC.presence_of_element_located(_search_bar_locator)
                )
                search_bar.send_keys("nimbus.qa.pref-1")
                wait.until(EC.presence_of_element_located(_row_locator))
                elements = selenium.find_elements(*_row_locator)
                assert wait_string in [element.text for element in elements]
            except Exception:
                time.sleep(2)
                return False
            else:
                return True

        return _wait_function

    requests.delete("http://ping-server:5000/pings")
    targeting = helpers.load_targeting_configs()[0]
    experiment_slug = str(slugify(experiment_name))
    experiment_default_data["targetingConfigSlug"] = targeting
    experiment_default_data["featureConfigId"] = 9
    experiment_default_data["referenceBranch"] = {
        "description": "reference branch",
        "name": "Branch 1",
        "ratio": 100,
        "featureEnabled": True,
        "featureValue": '{"value": "test_string_automation"}',
    }
    create_desktop_experiment(
        experiment_slug,
        "desktop",
        targeting,
        experiment_default_data,
    )

    wait.until(wait_function(selenium, "default"))

    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_live_status()

    # Ping the server twice as it sleeps sometimes
    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    # Check there was a telemetry event for the enrollment
    control = False
    timeout = time.time() + 60 * 5
    while control is not True:
        control = telemetry_event_check(experiment_slug, "enroll")
        if time.time() > timeout:
            assert False, "Experiment enrollment was never seen in ping Data"
    # check experiment exists, this means it is enrolled
    assert check_ping_for_experiment(experiment_slug), "Experiment not found in telemetry"

    wait.until(wait_function(selenium, "test_string_automation"))

    # unenroll
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_complete_status()

    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    control = False
    timeout = time.time() + 60 * 5
    while control is not True:
        control = telemetry_event_check(experiment_slug, "unenroll")
        if time.time() > timeout:
            assert False, "Experiment unenrollment was never seen in ping Data"

    wait.until(wait_function(selenium, "default"))
