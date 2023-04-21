from urllib.parse import urljoin

import pytest

from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage


@pytest.mark.remote_settings
def test_create_new_experiment_approve_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium, is_rollout=False).launch_and_approve()

    remote_settings_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()


@pytest.mark.remote_settings
def test_create_new_rollout_approve_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()


@pytest.mark.remote_settings
def test_create_new_experiment_reject_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium).launch_and_approve()

    remote_settings_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_create_new_rollout_reject_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_end_experiment_and_approve_end(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium).launch_and_approve()

    remote_settings_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    remote_settings_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_complete_status()


@pytest.mark.remote_settings
def test_end_rollout_and_approve_end(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    remote_settings_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_complete_status()


@pytest.mark.remote_settings
def test_end_experiment_and_reject_end(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium).launch_and_approve()

    remote_settings_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    remote_settings_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_end_rollout_and_reject_end(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    remote_settings_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
@pytest.mark.xdist_group(name="group2")
def test_takeaways(
    selenium,
    experiment_url,
    create_experiment,
    remote_settings_client,
):
    create_experiment(selenium).launch_and_approve()

    remote_settings_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    remote_settings_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    expected_summary = "Example takeaways summary text"
    summary.takeaways_edit_button.click()
    summary.takeaways_summary_field = expected_summary
    summary.takeaways_recommendation_radio_button("CHANGE_COURSE").click()
    summary.takeaways_save_button.click()

    assert summary.takeaways_summary_text == expected_summary
    assert summary.takeaways_recommendation_badge_text == "Change course"


@pytest.mark.remote_settings
@pytest.mark.xdist_group(name="group2")
def test_experiment_live_status_on_home_page(
    selenium, base_url, create_experiment, remote_settings_client, experiment_name, slugify
):
    experiment_slug = str(slugify(experiment_name))

    summary = create_experiment(selenium)
    summary.launch_and_approve()
    remote_settings_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_live_status()
    home = HomePage(selenium, base_url).open()
    assert True in [experiment_name in item.text for item in home.tables[0].experiments]


@pytest.mark.remote_settings
@pytest.mark.xdist_group(name="group2")
def test_rollout_live_status_on_home_page(
    selenium, base_url, create_experiment, remote_settings_client, experiment_name, slugify
):
    experiment_slug = str(slugify(experiment_name))

    create_experiment(selenium, is_rollout=True).launch_and_approve()
    remote_settings_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_live_status()
    home = HomePage(selenium, base_url).open()
    assert True in [experiment_name in item.text for item in home.tables[0].experiments]


@pytest.mark.remote_settings
def test_rollout_live_update_approve(
    selenium,
    base_url,
    create_experiment,
    remote_settings_client,
    experiment_name,
    slugify,
):
    experiment_slug = str(slugify(experiment_name))
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()

    summary.wait_for_live_status()
    audience = summary.navigate_to_audience()

    audience.percentage = "60"
    audience.save_and_continue()

    summary_page = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary_page.wait_for_update_request_visible()

    summary_page.request_update_and_approve()
    remote_settings_client.approve()


@pytest.mark.remote_settings
def test_rollout_live_update_approve_and_reject(
    selenium,
    base_url,
    create_experiment,
    remote_settings_client,
    experiment_name,
    slugify,
):
    experiment_slug = str(slugify(experiment_name))
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()

    summary.wait_for_live_status()
    audience = summary.navigate_to_audience()

    audience.percentage = "60"
    audience.save_and_continue()

    summary_page = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary_page.wait_for_update_request_visible()

    summary_page.request_update_and_approve()
    remote_settings_client.reject()

    summary_page.wait_for_rejection_notice_visible()


@pytest.mark.remote_settings
def test_rollout_create_and_update(
    selenium,
    base_url,
    create_experiment,
    remote_settings_client,
    experiment_name,
    slugify,
):
    experiment_slug = str(slugify(experiment_name))
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()

    summary.wait_for_live_status()
    audience = summary.navigate_to_audience()

    audience.percentage = "60"
    audience.save_and_continue()

    summary_page = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary_page.wait_for_update_request_visible()


@pytest.mark.remote_settings
def test_rollout_live_update_reject_on_experimenter(
    selenium,
    base_url,
    create_experiment,
    remote_settings_client,
    experiment_name,
    slugify,
):
    experiment_slug = str(slugify(experiment_name))
    create_experiment(selenium, is_rollout=True).launch_and_approve()

    remote_settings_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()

    summary.wait_for_live_status()
    audience = summary.navigate_to_audience()

    audience.percentage = "60"
    audience.save_and_continue()

    summary_page = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary_page.wait_for_update_request_visible()

    summary_page.request_update_and_reject()
    summary_page.wait_for_rejection_reason_text_input_visible()

    summary_page.set_rejection_reason()
    summary_page.submit_rejection()
    summary_page.wait_for_rejection_notice_visible()
