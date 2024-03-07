import time

import pytest
import requests

from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage


def navigate_to(selenium):
    demo_app_url = "http://demo-app-frontend:3000/"
    selenium.get(demo_app_url)


# @pytest.mark.cirrus_enrollment
# def test_create_new_rollout_approve_remote_settings_cirrus(
#     selenium,
#     experiment_url,
#     create_experiment,
#     kinto_client,
#     base_url,
#     experiment_name,
#     demo_app,
# ):
#     # Launch a rollout with 100% population
#     reference_branch_value = '{"enabled": true, "something": "You are enrolled"}'
#     create_experiment(
#         selenium, is_rollout=True, reference_branch_value=reference_branch_value
#     ).launch_and_approve()

#     kinto_client.approve()

#     SummaryPage(selenium, experiment_url).open().wait_for_live_status()

#     home = HomePage(selenium, base_url).open()
#     assert True in [experiment_name in item.text for item in home.tables[0].experiments]

#     # demo app frontend, default displays "Not Enrolled"
#     navigate_to(selenium)
#     selenium.refresh()
#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     # send client_id and context in a request to backend, backend will connect to
#     # cirrus and will return back the response
#     demo_app.fill_and_send_form_data("dummy_client_id", '{"test1":"test2"}')
#     demo_app.click_send_my_details()

#     # it should render "You are enrolled", reference branch value
#     result_text_element = demo_app.wait_for_result_text(["You are enrolled"])
#     assert result_text_element.is_displayed()

#     # Unenroll
#     summary = SummaryPage(selenium, experiment_url).open()
#     summary.end_and_approve()
#     kinto_client.approve()
#     summary = SummaryPage(selenium, experiment_url).open()
#     summary.wait_for_complete_status()

#     # Demo app frontend, default displays "Not Enrolled" again
#     navigate_to(selenium)
#     selenium.refresh()

#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     # Send the same client_id and context after the rollout has ended
#     demo_app.fill_and_send_form_data("dummy_client_id", '{"test1":"test2"}')
#     demo_app.click_send_my_details()

#     # returns the default value
#     result_text_element = demo_app.wait_for_result_text(["wicked"])
#     assert result_text_element.is_displayed()


# @pytest.mark.cirrus_enrollment
# def test_create_new_experiment_approve_remote_settings_cirrus(
#     selenium,
#     experiment_url,
#     create_experiment,
#     kinto_client,
#     base_url,
#     experiment_name,
#     demo_app,
# ):
#     # Launch an experiment with two branches
#     reference_branch_value = '{"enabled": true, "something": "Control branch"}'
#     treatment_branch_value = '{"enabled": true, "something": "Treatment branch"}'
#     create_experiment(
#         selenium,
#         reference_branch_value=reference_branch_value,
#         treatment_branch_value=treatment_branch_value,
#     ).launch_and_approve()

#     kinto_client.approve()

#     SummaryPage(selenium, experiment_url).open().wait_for_live_status()

#     home = HomePage(selenium, base_url).open()
#     assert True in [experiment_name in item.text for item in home.tables[0].experiments]

#     # Demo app frontend, by default, returns "Not Enrolled" message
#     navigate_to(selenium)
#     selenium.refresh()

#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     # Pass client_id and context
#     demo_app.fill_and_send_form_data("test", '{"test1":"test2"}')
#     demo_app.click_send_my_details()

#     # Determine the variation displayed and assert accordingly
#     # Check if either "Control branch" or "Treatment branch" is displayed
#     displayed_text = demo_app.wait_for_result_text(
#         ["Control branch", "Treatment branch"]
#     ).text
#     assert displayed_text in ["Control branch", "Treatment branch"]

#     # Refresh the page and try passing a new client
#     selenium.refresh()
#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     demo_app.fill_and_send_form_data("example1", '{"test1":"test2"}')
#     demo_app.click_send_my_details()

#     # Determine the variation displayed and assert accordingly
#     displayed_text = demo_app.wait_for_result_text(
#         ["Control branch", "Treatment branch"]
#     ).text
#     assert displayed_text in ["Control branch", "Treatment branch"]

#     # Unenroll
#     summary = SummaryPage(selenium, experiment_url).open()
#     summary.end_and_approve()
#     kinto_client.approve()
#     summary = SummaryPage(selenium, experiment_url).open()
#     summary.wait_for_complete_status()

#     navigate_to(selenium)
#     selenium.refresh()

#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     # Send the same client_id and context after the experiment has ended
#     demo_app.fill_and_send_form_data("example1", '{"test1":"test2"}')
#     demo_app.click_send_my_details()

#     # returns the default value
#     result_text_element = demo_app.wait_for_result_text(["wicked"])
#     assert result_text_element.is_displayed()

#     # Check another client id
#     selenium.refresh()
#     # Send the same client_id and context after the experiment has ended
#     demo_app.fill_and_send_form_data("test", '{"test1":"test2"}')
#     demo_app.click_send_my_details()

#     # returns the default value
#     result_text_element = demo_app.wait_for_result_text(["wicked"])
#     assert result_text_element.is_displayed()


# @pytest.mark.cirrus_enrollment
# def test_check_cirrus_targeting(
#     selenium,
#     experiment_url,
#     create_experiment,
#     kinto_client,
#     base_url,
#     experiment_name,
#     demo_app,
# ):
#     # Launch an experiment with two branches
#     reference_branch_value = '{"enabled": true, "something": "Control branch"}'
#     treatment_branch_value = '{"enabled": true, "something": "Treatment branch"}'
#     create_experiment(
#         selenium,
#         reference_branch_value=reference_branch_value,
#         treatment_branch_value=treatment_branch_value,
#         languages=True,
#         countries=True,
#     ).launch_and_approve()

#     kinto_client.approve()

#     SummaryPage(selenium, experiment_url).open().wait_for_live_status()

#     HomePage(selenium, base_url).open()

#     # Demo app frontend, by default, returns "Not Enrolled" message
#     navigate_to(selenium)
#     selenium.refresh()

#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     # Pass client_id and context
#     demo_app.fill_and_send_form_data("test", '{"language":"en", "region":"CA"}')
#     demo_app.click_send_my_details()

#     # Determine the variation displayed and assert accordingly
#     # Check if either "Control branch" or "Treatment branch" is displayed
#     displayed_text = demo_app.wait_for_result_text(
#         ["Control branch", "Treatment branch"]
#     ).text
#     assert displayed_text in ["Control branch", "Treatment branch"]

#     # Refresh the page and try passing a new client
#     selenium.refresh()
#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     demo_app.fill_and_send_form_data("example1", '{"language":"en", "region":"CA"}')
#     demo_app.click_send_my_details()

#     # Determine the variation displayed and assert accordingly
#     displayed_text = demo_app.wait_for_result_text(
#         ["Control branch", "Treatment branch"]
#     ).text
#     assert displayed_text in ["Control branch", "Treatment branch"]

#     # Unenroll
#     summary = SummaryPage(selenium, experiment_url).open()
#     summary.end_and_approve()
#     kinto_client.approve()
#     summary = SummaryPage(selenium, experiment_url).open()
#     summary.wait_for_complete_status()

#     navigate_to(selenium)
#     selenium.refresh()

#     result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
#     assert result_text_element.is_displayed()

#     # Send the same client_id and context after the experiment has ended
#     demo_app.fill_and_send_form_data("example1", '{"language":"en", "region":"CA"}')
#     demo_app.click_send_my_details()

#     # returns the default value
#     result_text_element = demo_app.wait_for_result_text(["wicked"])
#     assert result_text_element.is_displayed()

#     # Check another client id
#     selenium.refresh()
#     # Send the same client_id and context after the experiment has ended
#     demo_app.fill_and_send_form_data("test", '{"language":"en", "region":"CA"}')
#     demo_app.click_send_my_details()

#     # returns the default value
#     result_text_element = demo_app.wait_for_result_text(["wicked"])
#     assert result_text_element.is_displayed()


@pytest.mark.cirrus_enrollment
@pytest.mark.xdist_group(name="group1")
def test_check_telemetry_enrollment_unenrollment(
    selenium,
    kinto_client,
    telemetry_event_check,
    check_ping_for_experiment,
    experiment_slug,
    experiment_url,
    default_data_api,
    create_experiment,
    demo_app,
):
    # Launch an experiment with two branches
    reference_branch_value = '{"enabled": true, "something": "Control branch"}'
    treatment_branch_value = '{"enabled": true, "something": "Treatment branch"}'
    create_experiment(
        selenium,
        reference_branch_value=reference_branch_value,
        treatment_branch_value=treatment_branch_value,
    ).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()
    # Demo app frontend, by default, returns "Not Enrolled" message
    navigate_to(selenium)
    selenium.refresh()

    result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
    assert result_text_element.is_displayed()

    # Pass client_id and context
    demo_app.fill_and_send_form_data("test", '{"test1":"test2"}')
    demo_app.click_send_my_details()

    # Determine the variation displayed and assert accordingly
    # Check if either "Control branch" or "Treatment branch" is displayed
    displayed_text = demo_app.wait_for_result_text(
        ["Control branch", "Treatment branch"]
    ).text
    assert displayed_text in ["Control branch", "Treatment branch"]

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
    assert check_ping_for_experiment(
        experiment_slug
    ), "Experiment not found in telemetry"

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

    navigate_to(selenium)
    selenium.refresh()

    result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
    assert result_text_element.is_displayed()

    # Send the same client_id and context after the experiment has ended
    demo_app.fill_and_send_form_data("test", '{"test1":"test2"}')
    demo_app.click_send_my_details()

    # returns the default value
    result_text_element = demo_app.wait_for_result_text(["wicked"])
    assert result_text_element.is_displayed()

    requests.get("http://ping-server:5000/pings")
    time.sleep(5)

    control = False
    timeout = time.time() + 60 * 5
    while not control:
        control = telemetry_event_check(experiment_slug, "unenroll")
        if time.time() > timeout:
            raise AssertionError("Experiment enrollment was never seen in ping Data")
