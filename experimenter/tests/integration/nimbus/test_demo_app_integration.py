import os
import time
from kinto_http.utils import urljoin
from nimbus.pages.experimenter.home import HomePage
import pytest
from nimbus.pages.experimenter.summary import SummaryPage

def navigate_to_demo_app_frontend(selenium):
    demo_app_url = "http://demo-app-frontend:3000/"
    selenium.get(demo_app_url)

def fill_and_send_form_data(selenium, client_id, context):
    client_id_input = selenium.find_element_by_xpath("//input[@placeholder='Client ID']")
    context_input = selenium.find_element_by_xpath("//input[@placeholder='Context']")

    client_id_input.send_keys(client_id)
    context_input.send_keys(context)

def click_send_my_details(selenium):
    send_details_button = selenium.find_element_by_xpath("//button[contains(text(), 'Send My Details')]")
    assert send_details_button.is_displayed() and send_details_button.is_enabled()
    send_details_button.click()

@pytest.mark.demo_app
@pytest.mark.skipif(
    any(
        app in os.getenv("PYTEST_ARGS")
        for app in ["FOCUS_IOS", "IOS", "FENIX", "FOCUS_ANDROID", "FIREFOX_DESKTOP"]
    ),
    reason="Only run for cirrus applications",
)
def test_create_new_rollout_approve_remote_settings_demo_app(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
):
    # Launch a rollout with 100% population
    reference_branch_value = '{"enabled": true, "something": "You are enrolled"}'
    create_experiment(
        selenium, is_rollout=True, reference_branch_value=reference_branch_value
    ).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    home = HomePage(selenium, base_url).open()
    assert True in [experiment_name in item.text for item in home.tables[0].experiments]

    # demo app frontend, default displays not enrolled
    navigate_to_demo_app_frontend(selenium)
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Not Enrolled')]"
    )
    assert result_text_element.is_displayed()

    # send client_id and context in a request to backend, backend will connect to cirrus and will return back the response
    fill_and_send_form_data(selenium, "dummy_client_id", '{"test1":"test2"}')
    click_send_my_details(selenium)

    # it should render "You are enrolled", reference branch value
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'You are enrolled')]"
    )
    assert result_text_element.is_displayed()

    # unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    time.sleep(150)
    summary.wait_for_complete_status()

    # demo app frontend, default displays not enrolled
    navigate_to_demo_app_frontend(selenium)
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Not Enrolled')]"
    )
    assert result_text_element.is_displayed()

    # Send same client id and context, after rollout ended
    fill_and_send_form_data(selenium, "dummy_client_id", '{"test1":"test2"}')
    click_send_my_details(selenium)

    # returns the default value
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'wicked')]"
    )
    assert result_text_element.is_displayed()


@pytest.mark.demo_app
@pytest.mark.skipif(
    any(
        app in os.getenv("PYTEST_ARGS")
        for app in ["FOCUS_IOS", "IOS", "FENIX", "FOCUS_ANDROID", "FIREFOX_DESKTOP"]
    ),
    reason="Only run for cirrus applications",
)
def test_create_new_experiment_approve_remote_settings_demo_app(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
):
    # Launch an experiment with two branches
    reference_branch_value = '{"enabled": true, "something": "Control branch"}'
    treatment_branch_value = '{"enabled": true, "something": "Treatment branch"}'
    create_experiment(
        selenium, reference_branch_value=reference_branch_value, treatment_branch_value = treatment_branch_value
    ).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    home = HomePage(selenium, base_url).open()
    assert True in [experiment_name in item.text for item in home.tables[0].experiments]

    # demo app frontend, by default returns not enrolled message
    navigate_to_demo_app_frontend(selenium)
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Not Enrolled')]"
    )
    assert result_text_element.is_displayed()

    # pass client id and context
    fill_and_send_form_data(selenium, "example1", '{"test1":"test2"}')
    click_send_my_details(selenium)

    # user should be enrolled in control branch
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Control branch')]"
    )
    assert result_text_element.is_displayed()

    # Refresh page, and try passing new client
    selenium.refresh()
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Not Enrolled')]"
    )
    assert result_text_element.is_displayed()
    fill_and_send_form_data(selenium, "test1", '{"test1":"test2"}')
    click_send_my_details(selenium)

    # user should be enrolled in control branch
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Treatment branch')]"
    )
    assert result_text_element.is_displayed()

    # unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    time.sleep(150)
    summary.wait_for_complete_status()

    navigate_to_demo_app_frontend(selenium)

    # once experiment is ended, it should display default values

    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Not Enrolled')]"
    )
    assert result_text_element.is_displayed()
    fill_and_send_form_data(selenium, "example1", '{"test1":"test2"}') # previously enrolled in control branch
    click_send_my_details(selenium)
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'wicked')]"
    )
    assert result_text_element.is_displayed()

    # check another client id
    selenium.refresh()
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'Not Enrolled')]"
    )
    assert result_text_element.is_displayed()
    fill_and_send_form_data(selenium, "test1", '{"test1":"test2"}') # previously enrolled in treatment branch
    click_send_my_details(selenium)
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'wicked')]"
    )
    assert result_text_element.is_displayed()




