import os

from nimbus.pages.experimenter.home import HomePage
import pytest


from nimbus.pages.experimenter.summary import SummaryPage


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
    reference_branch_value = '{"enabled": true, "something": "You are enrolled"}'
    create_experiment(
        selenium, is_rollout=True, reference_branch_value=reference_branch_value
    ).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    home = HomePage(selenium, base_url).open()
    assert True in [experiment_name in item.text for item in home.tables[0].experiments]

    selenium.get("http://demo-app-frontend:3000/")

    # Example: Check if the "Send Details" button is present and clickable
    send_details_button = selenium.find_element_by_xpath(
        "//button[contains(text(), 'Send My Details')]"
    )
    assert send_details_button.is_displayed() and send_details_button.is_enabled()

    # # Example: Fill in form fields and click the button
    # client_id_input = selenium.find_element_by_xpath(
    #     "//input[@placeholder='Client ID']"
    # )
    # context_input = selenium.find_element_by_xpath("//input[@placeholder='Context']")
    # send_button = selenium.find_element_by_xpath(
    #     "//button[contains(text(), 'Send My Details')]"
    # )

    # client_id_input.send_keys("your_client_id")
    # context_input.send_keys("your_context")
    send_details_button.click()

    # Example: Wait for some result or text on the page
    result_text_element = selenium.find_element_by_xpath(
        "//h1[contains(text(), 'You are enrolled')]"
    )
    assert result_text_element.is_displayed()

    # Add more checks and interactions as needed

    # Finally, assert the expected behavior of the frontend based on your test case

    # Example: Assert that the displayed text is correct
    expected_text = "You are enrolled"
    actual_text = result_text_element.text
    assert expected_text == actual_text
