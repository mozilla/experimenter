import time

import pytest
from nimbus.pages.home import HomePage
from nimbus.pages.summary import SummaryPage
from nimbus.remote_settings.pages.dashboard import Dashboard
from nimbus.remote_settings.pages.login import Login
from selenium.common.exceptions import NoSuchElementException, TimeoutException


@pytest.mark.nondestructive
def test_create_new_experiment(selenium, base_url):
    experiment_name = "test_create_new_experiment"

    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_new_button()
    experiment.public_name = experiment_name
    experiment.hypothesis = "smart stuff here"
    experiment.application = "DESKTOP"

    # Fill Overview Page
    overview = experiment.save_and_continue()
    overview.public_description = "description stuff"
    overview.select_risk_brand_false()
    overview.select_risk_revenue_false()
    overview.select_risk_partner_false()

    # Fill Branches page
    branches = overview.save_and_continue()
    branches.remove_branch()
    branches.reference_branch_name = "name 1"
    branches.reference_branch_description = "a nice experiment"
    branches.feature_config = "No Feature Firefox Desktop"

    # Fill Metrics page
    metrics = branches.save_and_continue()

    # Fill Audience page
    audience = metrics.save_and_continue()
    audience.channel = "Nightly"
    audience.min_version = 80
    audience.targeting = "US_ONLY"
    audience.percentage = 50.0
    audience.expected_clients = 50
    audience.save_btn()
    audience.save_and_continue()

    # Review
    selenium.find_element_by_css_selector("#PageSummary")


def test_create_new_experiment_remote_settings(selenium, base_url):
    experiment_name = "test_create_new_experiment_remote_settings"

    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    current_experiments = None
    try:
        current_experiments = len(home.tables[0].experiments)
    except TimeoutException:
        current_experiments = 0
    experiment = home.create_new_button()
    experiment.public_name = experiment_name
    experiment.hypothesis = "smart stuff here"
    experiment.application = "DESKTOP"

    # Fill Overview Page
    overview = experiment.save_and_continue()
    overview.public_description = "description stuff"
    overview.select_risk_brand_false()
    overview.select_risk_revenue_false()
    overview.select_risk_partner_false()

    # Fill Branches page
    branches = overview.save_and_continue()
    branches.remove_branch()
    branches.reference_branch_name = "name 1"
    branches.reference_branch_description = "a nice experiment"
    branches.feature_config = "No Feature Firefox Desktop"

    # Fill Metrics page
    metrics = branches.save_and_continue()

    # Fill Audience page
    audience = metrics.save_and_continue()
    audience.channel = "Nightly"
    audience.min_version = 80
    audience.targeting = "US_ONLY"
    audience.percentage = 50.0
    audience.expected_clients = 50
    audience.save_btn()
    review = audience.save_and_continue()

    # Review and approve
    selenium.find_element_by_css_selector("#PageSummary")
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve()
    selenium.get("http://kinto:8888/v1/admin")
    kinto_login = Login(selenium, base_url).wait_for_page_to_load()
    kinto_login.kinto_auth.click()
    kinto_dashbard = kinto_login.login()
    bucket = kinto_dashbard.buckets[-1]
    for item in bucket.bucket_category:
        if "nimbus-desktop-experiments" in item.text:
            item.click()
            break
    record = kinto_dashbard.record
    record.action()
    selenium.get(base_url)
    # refresh until the experiment shows up
    for attempt in range(45):
        try:
            home = HomePage(selenium, base_url).wait_for_page_to_load()
            new_experiments = len(home.tables[0].experiments)
            assert new_experiments > current_experiments
        except AssertionError:
            time.sleep(2)
            selenium.refresh()
        else:
            break
    # Check it's live
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    live_experiments = home.tables[0]
    assert "live experiments" in live_experiments.table_name.lower()
    for item in live_experiments.experiments:
        if experiment_name in item.text:
            item.click()
            break
    summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
    assert "live" in summary_page.experiment_status.lower()


def test_create_new_experiment_remote_settings_reject(selenium, base_url):
    experiment_name = "test_create_new_experiment_remote_settings_reject"

    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    home.tabs[-1].click()  # Click drafts
    experiment = home.create_new_button()
    experiment.public_name = experiment_name
    experiment.hypothesis = "smart stuff here"
    experiment.application = "DESKTOP"

    # Fill Overview Page
    overview = experiment.save_and_continue()
    overview.public_description = "description stuff"
    overview.select_risk_brand_false()
    overview.select_risk_revenue_false()
    overview.select_risk_partner_false()

    # Fill Branches page
    branches = overview.save_and_continue()
    branches.remove_branch()
    branches.reference_branch_name = "name 1"
    branches.reference_branch_description = "a nice experiment"
    branches.feature_config = "No Feature Firefox Desktop"

    # Fill Metrics page
    metrics = branches.save_and_continue()

    # Fill Audience page
    audience = metrics.save_and_continue()
    audience.channel = "Nightly"
    audience.min_version = 80
    audience.targeting = "US_ONLY"
    audience.percentage = 50.0
    audience.expected_clients = 50
    audience.save_btn()
    review = audience.save_and_continue()

    # Review and approve
    selenium.find_element_by_css_selector("#PageSummary")
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve()
    selenium.get("http://kinto:8888/v1/admin")
    kinto_login = Login(selenium, base_url).wait_for_page_to_load()
    kinto_login.kinto_auth.click()
    kinto_dashbard = kinto_login.login()
    bucket = kinto_dashbard.buckets[-1]
    for item in bucket.bucket_category:
        if "nimbus-desktop-experiments" in item.text:
            item.click()
            break
    record = kinto_dashbard.record
    record.action("reject")
    kinto_dashbard = Dashboard(selenium, base_url)
    modal = kinto_dashbard.reject_modal
    modal.decline_changes()

    # Load home page and wait for experiment to show in the Drafts tab
    selenium.get(base_url)
    experiment_found = False
    for attempt in range(45):
        try:
            home = HomePage(selenium, base_url).wait_for_page_to_load()
            home.tabs[-1].click()
            new_experiments = home.tables[0].experiments
            for item in new_experiments:
                if experiment_name in item.text:
                    experiment_found = True
                    item.click()
                    break
            else:
                raise AssertionError
        except AssertionError:
            time.sleep(2)
            selenium.refresh()
        if experiment_found:
            break
    else:
        raise AssertionError("Experiment was not found")
    experiment_url = experiment_name.replace(" ", "-")
    selenium.get(f"{base_url}/{experiment_url}")
    for attempt in range(30):
        try:
            summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
            assert summary_page.rejected_text, "Rejected text box did not load"
            break
        except NoSuchElementException:
            time.sleep(2)
            selenium.refresh()
    else:
        raise AssertionError("Experiment page didn't load")


def test_create_new_experiment_remote_settings_timeout(selenium, base_url):
    experiment_name = "test_create_new_experiment_remote_settings_timeout"

    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_new_button()
    experiment.public_name = experiment_name
    experiment.hypothesis = "smart stuff here"
    experiment.application = "DESKTOP"

    # Fill Overview Page
    overview = experiment.save_and_continue()
    overview.public_description = "description stuff"
    overview.select_risk_brand_false()
    overview.select_risk_revenue_false()
    overview.select_risk_partner_false()

    # Fill Branches page
    branches = overview.save_and_continue()
    branches.remove_branch()
    branches.reference_branch_name = "name 1"
    branches.reference_branch_description = "a nice experiment"
    branches.feature_config = "No Feature Firefox Desktop"

    # Fill Metrics page
    metrics = branches.save_and_continue()

    # Fill Audience page
    audience = metrics.save_and_continue()
    audience.channel = "Nightly"
    audience.min_version = 80
    audience.targeting = "US_ONLY"
    audience.percentage = 50.0
    audience.expected_clients = 50
    audience.save_btn()
    review = audience.save_and_continue()

    # Review and approve
    selenium.find_element_by_css_selector("#PageSummary")
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve()
    for attempt in range(60):
        try:
            review = SummaryPage(selenium, base_url).wait_for_page_to_load()
            review.timeout_text
        except NoSuchElementException:
            time.sleep(2)
            selenium.refresh()
        else:
            assert review.timeout_text, "Timeout text not shown."
            break
    else:
        raise AssertionError("Timeout text was never shown.")
