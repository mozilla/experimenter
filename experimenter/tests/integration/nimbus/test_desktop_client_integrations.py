import time

import pytest
import requests

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.browser import AboutConfig
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
    firefox_options.set_preference("sticky.targeting.test.pref", True)
    firefox_options.set_preference("toolkit.telemetry.log.level", "Trace")
    firefox_options.set_preference("toolkit.telemetry.log.dump", True)
    firefox_options.set_preference("toolkit.telemetry.send.overrideOfficialCheck", True)
    firefox_options.set_preference("toolkit.telemetry.testing.disableFuzzingDelay", True)
    firefox_options.set_preference("nimbus.debug", True)
    firefox_options.set_preference("app.normandy.run_interval_seconds", 30)
    firefox_options.set_preference(
        "security.content.signature.root_hash",
        "5E:36:F2:14:DE:82:3F:8B:29:96:89:23:5F:03:41:AC:AF:A0:75:AF:82:CB:4C:D4:30:7C:3D:B3:43:39:2A:FE",
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


@pytest.mark.desktop_enrollment
@pytest.mark.xdist_group(name="group1")
def test_check_telemetry_enrollment_unenrollment(
    selenium,
    kinto_client,
    telemetry_event_check,
    check_ping_for_experiment,
    experiment_slug,
    experiment_url,
    default_data_api,
):
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        default_data_api,
    )
    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()

    # Ping the server twice as it sleeps sometimes
    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    # Check their was a telemetry event for the enrollment
    control = False
    timeout = time.time() + 60 * 5
    while not control:
        control = telemetry_event_check(experiment_slug, "enroll")
        if time.time() > timeout:
            raise AssertionError("Experiment enrollment was never seen in ping Data")
    # check experiment exists, this means it is enrolled
    assert check_ping_for_experiment(experiment_slug), "Experiment not found in telemetry"

    # check experiment exists, this means it is enrolled
    assert check_ping_for_experiment(experiment_slug)
    for item in requests.get("http://ping-server:5000/pings").json():
        if "experiments" in item["environment"]:
            for key in item["environment"]["experiments"]:
                if experiment_slug in key:
                    break

    # unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    control = False
    timeout = time.time() + 60 * 5
    while not control:
        control = telemetry_event_check(experiment_slug, "unenroll")
        if time.time() > timeout:
            raise AssertionError("Experiment enrollment was never seen in ping Data")


@pytest.mark.desktop_enrollment
@pytest.mark.xdist_group(name="group2")
def test_check_telemetry_pref_flip(
    selenium,
    kinto_client,
    default_data_api,
    check_ping_for_experiment,
    telemetry_event_check,
    trigger_experiment_loader,
    experiment_slug,
    experiment_url,
):
    about_config = AboutConfig(selenium)

    default_data_api["featureConfigIds"] = [9]
    default_data_api["referenceBranch"] = {
        "description": "reference branch",
        "name": "Branch 1",
        "ratio": 100,
        "featureValues": [
            {
                "featureConfig": "9",
                "value": '{"value": "test_string_automation"}',
            },
        ],
    }
    default_data_api["treatmentBranches"] = []
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        default_data_api,
    )

    about_config = about_config.open().wait_for_page_to_load()
    about_config.wait_for_pref_flip(
        "nimbus.qa.pref-1", "default", action=trigger_experiment_loader
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()

    # Ping the server twice as it sleeps sometimes
    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    # Check there was a telemetry event for the enrollment
    control = False
    timeout = time.time() + 60 * 5
    while not control:
        control = telemetry_event_check(experiment_slug, "enroll")
        if time.time() > timeout:
            raise AssertionError("Experiment enrollment was never seen in ping Data")
    # check experiment exists, this means it is enrolled
    assert check_ping_for_experiment(experiment_slug), "Experiment not found in telemetry"

    about_config = about_config.open().wait_for_page_to_load()
    about_config.wait_for_pref_flip(
        "nimbus.qa.pref-1", "test_string_automation", action=trigger_experiment_loader
    )

    # unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    control = False
    timeout = time.time() + 60 * 5
    while not control:
        control = telemetry_event_check(experiment_slug, "unenroll")
        if time.time() > timeout:
            raise AssertionError("Experiment unenrollment was never seen in ping Data")

    about_config = about_config.open().wait_for_page_to_load()
    about_config.wait_for_pref_flip(
        "nimbus.qa.pref-1", "default", action=trigger_experiment_loader
    )


@pytest.mark.desktop_enrollment
@pytest.mark.xdist_group(name="group1")
def test_check_telemetry_sticky_targeting(
    selenium,
    kinto_client,
    default_data_api,
    check_ping_for_experiment,
    telemetry_event_check,
    trigger_experiment_loader,
    experiment_slug,
    experiment_url,
):
    about_config = AboutConfig(selenium)
    pref_name = "sticky.targeting.test.pref"

    requests.delete("http://ping-server:5000/pings")
    targeting_config_slug = "no_targeting"
    default_data_api["targetingConfigSlug"] = targeting_config_slug
    default_data_api["referenceBranch"] = {
        "description": "reference branch",
        "name": "Branch 1",
        "ratio": 100,
        "featureValues": [
            {
                "featureConfig": "1",
                "value": "{}",
            },
        ],
    }
    default_data_api["treatmentBranches"] = []
    default_data_api["isSticky"] = True
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        default_data_api,
        targeting=targeting_config_slug,
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()

    # Ping the server twice as it sleeps sometimes
    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    # Check there was a telemetry event for the enrollment
    control = False
    timeout = time.time() + 60 * 5
    while not control:
        control = telemetry_event_check(experiment_slug, "enroll")
        if time.time() > timeout:
            raise AssertionError("Experiment enrollment was never seen in ping Data")
    # check experiment exists, this means it is enrolled
    assert check_ping_for_experiment(experiment_slug), "Experiment not found in telemetry"

    # flip pref
    about_config = about_config.open().wait_for_page_to_load()
    about_config.wait_for_pref_flip(
        pref_name, True, action=trigger_experiment_loader, pref_type=bool
    )
    about_config.flip_pref(pref_name)

    assert about_config.get_pref_value(pref_name) == "false"

    # check experiment doesn't unenroll after pref flip
    control = False
    timeout = time.time() + 60
    while not control and time.time() < timeout:
        control = telemetry_event_check(experiment_slug, "unenroll")
        if control:
            raise AssertionError("Experiment unenrolled when it shouldn't have")
    assert check_ping_for_experiment(experiment_slug), "Experiment not found in telemetry"

    # unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    # check for unenroll event after experiment is ended
    control = False
    timeout = time.time() + 60 * 5
    while not control:
        control = telemetry_event_check(experiment_slug, "unenroll")
        if time.time() > timeout:
            raise AssertionError("Experiment unenrollment was never seen in ping Data")

    # check pref still matches user change
    assert about_config.get_pref_value(pref_name) == "false"
