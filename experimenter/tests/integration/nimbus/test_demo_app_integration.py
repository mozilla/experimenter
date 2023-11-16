import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage


class DemoAppPage:
    def __init__(self, driver):
        self.driver = driver

    def navigate_to(self):
        demo_app_url = "http://demo-app-frontend:3000/"
        self.driver.get(demo_app_url)

    def wait_for_result_text(self, text_list):
        xpath_conditions = " | ".join(
            [f"contains(text(), '{text}')" for text in text_list]
        )
        xpath = f"//h1[{xpath_conditions}]"

        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

    def fill_and_send_form_data(self, client_id, context):
        time.sleep(10)
        client_id_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Client ID']")
            )
        )
        context_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Context']"))
        )

        client_id_input.send_keys(client_id)
        context_input.send_keys(context)

    def click_send_my_details(self):
        send_details_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Send My Details')]")
            )
        )
        assert send_details_button.is_displayed() and send_details_button.is_enabled()
        send_details_button.click()


@pytest.mark.demo_app
def test_create_new_rollout_approve_remote_settings_demo_app(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
    driver,
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

    # demo app frontend, default displays "Not Enrolled"
    demo_app = DemoAppPage(driver)

    demo_app.navigate_to()
    result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
    assert result_text_element.is_displayed()

    # send client_id and context in a request to backend, backend will connect to
    # cirrus and will return back the response
    demo_app.fill_and_send_form_data("dummy_client_id", '{"test1":"test2"}')
    demo_app.click_send_my_details()

    # it should render "You are enrolled", reference branch value
    result_text_element = demo_app.wait_for_result_text(["You are enrolled"])
    assert result_text_element.is_displayed()

    # Unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    # Demo app frontend, default displays "Not Enrolled" again
    demo_app.navigate_to()
    selenium.refresh()

    result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
    assert result_text_element.is_displayed()

    # Send the same client_id and context after the rollout has ended
    demo_app.fill_and_send_form_data("dummy_client_id", '{"test1":"test2"}')
    demo_app.click_send_my_details()

    # returns the default value
    result_text_element = demo_app.wait_for_result_text(["wicked"])
    assert result_text_element.is_displayed()


@pytest.mark.demo_app
def test_create_new_experiment_approve_remote_settings_demo_app(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
    driver
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

    home = HomePage(selenium, base_url).open()
    assert True in [experiment_name in item.text for item in home.tables[0].experiments]

    demo_app = DemoAppPage(driver)
    # Demo app frontend, by default, returns "Not Enrolled" message
    demo_app.navigate_to()

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

    # Refresh the page and try passing a new client
    selenium.refresh()
    result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
    assert result_text_element.is_displayed()

    demo_app.fill_and_send_form_data("example1", '{"test1":"test2"}')
    demo_app.click_send_my_details()

    # Determine the variation displayed and assert accordingly
    displayed_text = demo_app.wait_for_result_text(
        ["Control branch", "Treatment branch"]
    ).text
    assert displayed_text in ["Control branch", "Treatment branch"]

    # Unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    demo_app.navigate_to()
    selenium.refresh()

    result_text_element = demo_app.wait_for_result_text(["Not Enrolled"])
    assert result_text_element.is_displayed()

    # Send the same client_id and context after the experiment has ended
    demo_app.fill_and_send_form_data("example1", '{"test1":"test2"}')
    demo_app.click_send_my_details()

    # returns the default value
    result_text_element = demo_app.wait_for_result_text(["wicked"])
    assert result_text_element.is_displayed()

    # Check another client id
    selenium.refresh()
    # Send the same client_id and context after the experiment has ended
    demo_app.fill_and_send_form_data("test", '{"test1":"test2"}')
    demo_app.click_send_my_details()

    # returns the default value
    result_text_element = demo_app.wait_for_result_text(["wicked"])
    assert result_text_element.is_displayed()
