import pytest

from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage


def navigate_to(selenium):
    demo_app_url = "http://demo-app-frontend:3000/"
    selenium.get(demo_app_url)


@pytest.mark.cirrus_enrollment
def test_create_new_rollout_approve_remote_settings_cirrus(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
    demo_app,
):
    # Launch a rollout with 100% population
    create_experiment(
        selenium,
        is_rollout=True,
        reference_branch_value=demo_app.REFERENCE_BRANCH_VALUE,
    ).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    HomePage(selenium, base_url).open().find_in_table(experiment_name)

    # Demo app frontend, default displays "Not Enrolled"
    navigate_to(selenium)
    selenium.refresh()
    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Send client_id and context to backend
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_1["client_id"], demo_app.CLIENT_1["context"]
    )

    # Should render "You are enrolled"
    assert demo_app.wait_for_result_text([demo_app.CONTROL_BRANCH]).is_displayed()

    # Unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    # Demo app frontend, default displays "Not Enrolled" again
    navigate_to(selenium)
    selenium.refresh()
    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Send the same client_id and context after the rollout has ended
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_1["client_id"], demo_app.CLIENT_1["context"]
    )

    # Returns the default value
    assert demo_app.wait_for_result_text([demo_app.DEFAULT_WICKED_TEXT]).is_displayed()


@pytest.mark.cirrus_enrollment
def test_create_new_experiment_approve_remote_settings_cirrus(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
    demo_app,
):
    # Launch an experiment with two branches
    create_experiment(
        selenium,
        reference_branch_value=demo_app.REFERENCE_BRANCH_VALUE,
        treatment_branch_value=demo_app.TREATMENT_BRANCH_VALUE,
    ).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    HomePage(selenium, base_url).open().find_in_table(experiment_name)

    # Demo app frontend, by default, returns "Not Enrolled" message
    navigate_to(selenium)
    selenium.refresh()

    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Pass client_id and context
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_1["client_id"], demo_app.CLIENT_1["context"]
    )

    # Determine the variation displayed and assert accordingly
    displayed_text = demo_app.wait_for_result_text(
        [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]
    ).text
    assert displayed_text in [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]

    # Refresh the page and try passing a new client
    selenium.refresh()
    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_2["client_id"], demo_app.CLIENT_2["context"]
    )

    # Determine the variation displayed and assert accordingly
    displayed_text = demo_app.wait_for_result_text(
        [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]
    ).text
    assert displayed_text in [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]

    # Unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    navigate_to(selenium)
    selenium.refresh()

    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Send the same client_id and context after the experiment has ended
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_2["client_id"], demo_app.CLIENT_2["context"]
    )

    # Returns the default value
    assert demo_app.wait_for_result_text([demo_app.DEFAULT_WICKED_TEXT]).is_displayed()

    # Check another client id
    selenium.refresh()
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_1["client_id"], demo_app.CLIENT_1["context"]
    )

    # Returns the default value
    assert demo_app.wait_for_result_text([demo_app.DEFAULT_WICKED_TEXT]).is_displayed()


@pytest.mark.cirrus_enrollment
def test_check_cirrus_targeting(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
    demo_app,
):
    # Launch an experiment with two branches
    create_experiment(
        selenium,
        reference_branch_value=demo_app.REFERENCE_BRANCH_VALUE,
        treatment_branch_value=demo_app.TREATMENT_BRANCH_VALUE,
        languages=True,
        countries=True,
    ).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    HomePage(selenium, base_url).open()

    # Demo app frontend, by default, returns "Not Enrolled" message
    navigate_to(selenium)
    selenium.refresh()

    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Pass client_id and context
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_3["client_id"], demo_app.CLIENT_3["context"]
    )

    # Determine the variation displayed and assert accordingly
    displayed_text = demo_app.wait_for_result_text(
        [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]
    ).text
    assert displayed_text in [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]

    # Refresh the page and try passing a new client
    selenium.refresh()
    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_2["client_id"], demo_app.CLIENT_3["context"]
    )

    # Determine the variation displayed and assert accordingly
    displayed_text = demo_app.wait_for_result_text(
        [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]
    ).text
    assert displayed_text in [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]

    # Unenroll
    summary = SummaryPage(selenium, experiment_url).open()
    summary.end_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    navigate_to(selenium)
    selenium.refresh()

    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Send the same client_id and context after the experiment has ended
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_3["client_id"], demo_app.CLIENT_3["context"]
    )

    # Returns the default value
    assert demo_app.wait_for_result_text([demo_app.DEFAULT_WICKED_TEXT]).is_displayed()

    # Check another client id
    selenium.refresh()
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_1["client_id"], demo_app.CLIENT_3["context"]
    )

    # Returns the default value
    assert demo_app.wait_for_result_text([demo_app.DEFAULT_WICKED_TEXT]).is_displayed()


@pytest.mark.cirrus_enrollment
def test_nimbus_preview_flag(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
    base_url,
    experiment_name,
    demo_app,
):
    create_experiment(
        selenium,
        reference_branch_value=demo_app.REFERENCE_BRANCH_VALUE,
        treatment_branch_value=demo_app.TREATMENT_BRANCH_VALUE,
    ).launch_to_preview()

    SummaryPage(selenium, experiment_url).open().wait_for_preview_status()

    navigate_to(selenium)
    selenium.refresh()
    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Enable nimbus preview flag
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_1["client_id"],
        demo_app.CLIENT_1["context"],
        nimbus_preview=True,
    )

    displayed_text = demo_app.wait_for_result_text(
        [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]
    ).text
    assert displayed_text in [demo_app.CONTROL_BRANCH, demo_app.TREATMENT_BRANCH]

    navigate_to(selenium)
    selenium.refresh()
    assert demo_app.wait_for_result_text(
        [demo_app.DEFAULT_NOT_ENROLLED_TEXT]
    ).is_displayed()

    # Not using nimbus preview flag
    demo_app.fill_and_send_form_data(
        demo_app.CLIENT_2["client_id"], demo_app.CLIENT_2["context"]
    )

    assert demo_app.wait_for_result_text([demo_app.DEFAULT_WICKED_TEXT]).is_displayed()
