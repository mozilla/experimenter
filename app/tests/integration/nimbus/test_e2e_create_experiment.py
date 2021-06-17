
import random
import time

import pytest
from selenium.common.exceptions import NoSuchElementException
from nimbus.pages.home import HomePage
from nimbus.pages.summary import SummaryPage
from nimbus.pages.review import ReviewPage
from nimbus.remote_settings.pages.login import Login
from nimbus.remote_settings.pages.dashboard import Dashboard


@pytest.mark.nondestructive
def test_create_new_experiment(selenium, base_url):
    experiment_name = f"name here remote {random.randint(0, 100)}"

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
    selenium.find_element_by_css_selector("#PageRequestReview")


def test_create_new_experiment_remote_settings(selenium, base_url):
    experiment_name = f"name here remote {random.randint(0, 1000)}"

    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    current_experiments = len(home.tables[0].experiments)
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
    selenium.find_element_by_css_selector("#PageRequestReview")
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
            assert new_experiments != current_experiments
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


def test_create_new_experiment_remote_settings1(selenium, base_url):
    experiment_name = f"name here remote {random.randint(0, 1000)}"

    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    home.tabs[-1].click()  # Click drafts
    current_experiments = len(home.tables[0].experiments)
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
    selenium.find_element_by_css_selector("#PageRequestReview")
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
    selenium.get(base_url)
    for attempt in range(45):
        try:
            home = HomePage(selenium, base_url).wait_for_page_to_load()
            home.tabs[-1].click()
            new_experiments = len(home.tables[0].experiments)
            assert new_experiments != current_experiments
        except AssertionError:
            time.sleep(2)
            selenium.refresh()
        else:
            break
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    home.tabs[-1].click()
    draft_experiments = home.tables[0]
    for item in draft_experiments.experiments:
        if experiment_name in item.text:
            item.click()
            break
    # TEMP FIX
    experiment_url = experiment_name.replace(" ", "-")
    print(experiment_url)
    selenium.get(f"{base_url}/{experiment_url}/request-review")
    for attempt in range(30):
        try:
            summary_page = ReviewPage(selenium, base_url).wait_for_page_to_load()
            assert summary_page.rejected_text, "Rejected text box did not load"
        except NoSuchElementException:
            time.sleep(2)
            selenium.refresh()
