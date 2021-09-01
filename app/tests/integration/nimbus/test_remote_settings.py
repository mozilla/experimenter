import pytest
from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.pages.remote_settings.dashboard import Dashboard
from nimbus.pages.remote_settings.login import Login


@pytest.mark.run_per_app
def test_create_new_experiment_approve_remote_settings(
    selenium,
    base_url,
    kinto_url,
    kinto_review_url,
    experiment_url,
    default_data,
    create_experiment,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()

    summary = create_experiment(selenium, home, default_data)
    summary.launch_without_preview.click()
    summary.request_review.click_launch_checkboxes()
    summary.request_review.request_launch_button.click()
    summary.approve()

    selenium.get(kinto_url)
    kinto_login = Login(selenium, kinto_url).wait_for_page_to_load()
    kinto_login.login()

    selenium.get(kinto_review_url)
    kinto_dashboard = Dashboard(selenium, kinto_review_url).wait_for_page_to_load()
    kinto_dashboard.approve()

    selenium.get(experiment_url)
    summary = SummaryPage(selenium, experiment_url).wait_for_page_to_load()
    summary.wait_for_live_status()


@pytest.mark.run_once
def test_create_new_experiment_reject_remote_settings(
    selenium,
    base_url,
    kinto_url,
    kinto_review_url,
    experiment_url,
    default_data,
    create_experiment,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()

    summary = create_experiment(selenium, home, default_data)
    summary.launch_without_preview.click()
    summary.request_review.click_launch_checkboxes()
    summary.request_review.request_launch_button.click()
    summary.approve()

    selenium.get(kinto_url)
    kinto_login = Login(selenium, kinto_url).wait_for_page_to_load()
    kinto_login.login()

    selenium.get(kinto_review_url)
    kinto_dashboard = Dashboard(selenium, kinto_review_url).wait_for_page_to_load()
    kinto_dashboard.reject()

    selenium.get(experiment_url)
    summary = SummaryPage(selenium, experiment_url).wait_for_page_to_load()
    summary.wait_for_rejected_alert()


@pytest.mark.run_once
def test_create_new_experiment_timeout_remote_settings(
    selenium,
    base_url,
    default_data,
    create_experiment,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()

    summary = create_experiment(selenium, home, default_data)
    summary.launch_without_preview.click()
    summary.request_review.click_launch_checkboxes()
    summary.request_review.request_launch_button.click()
    summary.approve()

    summary.wait_for_timeout_alert()


@pytest.mark.run_once
def test_end_experiment_and_approve_end(
    selenium,
    base_url,
    kinto_url,
    kinto_review_url,
    experiment_url,
    default_data,
    create_experiment,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()

    summary = create_experiment(selenium, home, default_data)
    summary.launch_without_preview.click()
    summary.request_review.click_launch_checkboxes()
    summary.request_review.request_launch_button.click()
    summary.approve()

    selenium.get(kinto_url)
    kinto_login = Login(selenium, kinto_url).wait_for_page_to_load()
    kinto_login.login()

    selenium.get(kinto_review_url)
    kinto_dashboard = Dashboard(selenium, kinto_review_url).wait_for_page_to_load()
    kinto_dashboard.approve()

    selenium.get(experiment_url)
    summary = SummaryPage(selenium, experiment_url).wait_for_page_to_load()
    summary.wait_for_live_status()
    summary.end_experiment()
    summary.approve()

    selenium.get(kinto_review_url)
    kinto_dashboard = Dashboard(selenium, kinto_review_url).wait_for_page_to_load()
    kinto_dashboard.approve()

    selenium.get(experiment_url)
    summary = SummaryPage(selenium, experiment_url).wait_for_page_to_load()
    summary.wait_for_complete_status()


@pytest.mark.run_once
def test_end_experiment_and_reject_end(
    selenium,
    base_url,
    kinto_url,
    kinto_review_url,
    experiment_url,
    default_data,
    create_experiment,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()

    summary = create_experiment(selenium, home, default_data)
    summary.launch_without_preview.click()
    summary.request_review.click_launch_checkboxes()
    summary.request_review.request_launch_button.click()
    summary.approve()

    selenium.get(kinto_url)
    kinto_login = Login(selenium, kinto_url).wait_for_page_to_load()
    kinto_login.login()

    selenium.get(kinto_review_url)
    kinto_dashboard = Dashboard(selenium, kinto_review_url).wait_for_page_to_load()
    kinto_dashboard.approve()

    selenium.get(experiment_url)
    summary = SummaryPage(selenium, experiment_url).wait_for_page_to_load()
    summary.wait_for_live_status()
    summary.end_experiment()
    summary.approve()

    selenium.get(kinto_review_url)
    kinto_dashboard = Dashboard(selenium, kinto_review_url).wait_for_page_to_load()
    kinto_dashboard.reject()

    selenium.get(experiment_url)
    summary = SummaryPage(selenium, experiment_url).wait_for_page_to_load()
    summary.wait_for_rejected_alert()
