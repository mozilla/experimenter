from urllib.parse import urljoin

import pytest
from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage


@pytest.mark.remote_settings
def test_create_new_experiment_approve_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()


@pytest.mark.remote_settings
def test_create_new_experiment_reject_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
def test_end_experiment_and_approve_end(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_complete_status()


@pytest.mark.remote_settings
def test_end_experiment_and_reject_end(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.remote_settings
@pytest.mark.xdist_group(name="group2")
def test_takeaways(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.approve()

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
def test_check_live_status_on_home_page(
    selenium, base_url, create_experiment, kinto_client, experiment_name, slugify
):
    experiment_slug = str(slugify(experiment_name))

    summary = create_experiment(selenium)
    summary.launch_and_approve()
    kinto_client.approve()
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_live_status()
    home = HomePage(selenium, base_url).open()
    assert True in [experiment_name in item.text for item in home.tables[0].experiments]
