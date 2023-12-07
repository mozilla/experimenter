import pytest

from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers


@pytest.mark.remote_settings
def test_create_new_experiment_approve_remote_settings(
    selenium,
    experiment_url,
    kinto_client,
    base_url,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(experiment_slug, application, default_data_api)

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    home = HomePage(selenium, base_url).open()
    assert experiment_slug in [item.text for item in home.tables[0].experiments]


@pytest.mark.remote_settings
def test_create_new_rollout_approve_remote_settings(
    selenium,
    experiment_url,
    kinto_client,
    base_url,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(
        experiment_slug, application, default_data_api, is_rollout=True
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()

    home = HomePage(selenium, base_url).open()
    assert experiment_slug in [item.text for item in home.tables[0].experiments]


@pytest.mark.remote_settings
def test_create_new_experiment_reject_remote_settings(
    selenium,
    experiment_url,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(experiment_slug, application, default_data_api)

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_create_new_rollout_reject_remote_settings(
    selenium,
    experiment_url,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(
        experiment_slug, application, default_data_api, is_rollout=True
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_end_experiment_and_approve_end_set_takeaways(
    selenium,
    experiment_url,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(experiment_slug, application, default_data_api)

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    takeaways = "Example takeaways summary text"
    summary.set_takeaways(takeaways, "CHANGE_COURSE")

    assert summary.takeaways_summary_text == takeaways
    assert summary.takeaways_recommendation_badge_text == "Change course"


@pytest.mark.remote_settings
def test_end_rollout_and_approve_end_set_takeaways(
    selenium,
    experiment_url,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(
        experiment_slug, application, default_data_api, is_rollout=True
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    takeaways = "Example takeaways summary text"
    summary.set_takeaways(takeaways, "CHANGE_COURSE")

    assert summary.takeaways_summary_text == takeaways
    assert summary.takeaways_recommendation_badge_text == "Change course"


@pytest.mark.remote_settings
def test_end_experiment_and_reject_end(
    selenium,
    experiment_url,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(experiment_slug, application, default_data_api)

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_end_rollout_and_reject_end(
    selenium,
    experiment_url,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
):
    helpers.create_experiment(
        experiment_slug, application, default_data_api, is_rollout=True
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_rollout_live_update_approve(
    selenium,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
    experiment_url,
):
    helpers.create_experiment(
        experiment_slug, application, default_data_api, is_rollout=True
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()

    summary.wait_for_live_status()
    audience = summary.navigate_to_audience()

    audience.percentage = "60"
    summary = audience.save_and_continue()

    summary.wait_for_update_request_visible()
    summary.request_update_and_approve()
    kinto_client.approve()


@pytest.mark.remote_settings
def test_rollout_live_update_approve_and_reject(
    selenium,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
    experiment_url,
):
    helpers.create_experiment(
        experiment_slug, application, default_data_api, is_rollout=True
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()

    summary.wait_for_live_status()
    audience = summary.navigate_to_audience()

    audience.percentage = "60"
    summary = audience.save_and_continue()

    summary.wait_for_update_request_visible()

    summary.request_update_and_approve()
    kinto_client.reject()

    summary.wait_for_rejection_notice_visible()


@pytest.mark.remote_settings
def test_rollout_live_update_reject_on_experimenter(
    selenium,
    kinto_client,
    application,
    default_data_api,
    experiment_slug,
    experiment_url,
):
    helpers.create_experiment(
        experiment_slug, application, default_data_api, is_rollout=True
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()
    summary = SummaryPage(selenium, experiment_url).open()

    summary.wait_for_live_status()
    audience = summary.navigate_to_audience()

    audience.percentage = "60"
    summary = audience.save_and_continue()

    summary.wait_for_update_request_visible()

    summary.request_update_and_reject()
    summary.wait_for_rejection_reason_text_input_visible()

    summary.set_rejection_reason()
    summary.submit_rejection()
    summary.wait_for_rejection_notice_visible()


@pytest.mark.remote_settings
def test_create_new_experiment_timeout_remote_settings(
    selenium,
    application,
    default_data_api,
    experiment_slug,
    experiment_url,
):
    helpers.create_experiment(experiment_slug, application, default_data_api)

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()
    summary.wait_for_timeout_alert()
