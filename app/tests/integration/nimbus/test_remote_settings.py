import time

import pytest
from nimbus.pages.home import HomePage
from nimbus.pages.summary import SummaryPage
from selenium.common.exceptions import NoSuchElementException, TimeoutException


@pytest.mark.run_per_app
def test_create_new_experiment_approve_remote_settings(
    selenium,
    base_url,
    default_data,
    create_experiment,
    perform_kinto_action,
    timeout_length,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    current_experiments = None
    try:
        current_experiments = len(home.tables[0].experiments)
    except TimeoutException:
        current_experiments = 0

    review = create_experiment(selenium, home, default_data)
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve(timeout_length)

    perform_kinto_action(selenium, base_url, "approve")

    selenium.get(base_url)
    # refresh until the experiment shows up
    for attempt in range(timeout_length):
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
    assert "Live" in home.active_tab_text
    for item in live_experiments.experiments:
        if default_data.public_name in item.text:
            item.click()
            break
    summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
    assert "live" in summary_page.experiment_status.lower()


@pytest.mark.run_once
def test_create_new_experiment_reject_remote_settings(
    selenium,
    base_url,
    default_data,
    create_experiment,
    perform_kinto_action,
    timeout_length,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    home.tabs[-1].click()  # Click drafts
    review = create_experiment(selenium, home, default_data)
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve(timeout_length)

    perform_kinto_action(selenium, base_url, "reject")

    # Load home page and wait for experiment to show in the Drafts tab
    drafts_tab_url = f"{base_url}?tab=drafts"
    selenium.get(drafts_tab_url)
    experiment_found = False
    for attempt in range(timeout_length):
        try:
            home = HomePage(selenium, drafts_tab_url).wait_for_page_to_load()
            new_experiments = home.tables[0].experiments
            for item in new_experiments:
                if default_data.public_name in item.text:
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
    url = (
        default_data.public_name.lower()
        .replace(" ", "-")
        .replace("[", "")
        .replace("]", "")
    )
    selenium.get(f"{base_url}/{url}")
    for attempt in range(timeout_length):
        try:
            summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
            assert summary_page.rejected_text, "Rejected text box did not load"
            break
        except NoSuchElementException:
            time.sleep(2)
            selenium.refresh()
    else:
        raise AssertionError("Experiment page didn't load")


@pytest.mark.run_once
def test_create_new_experiment_timeout_remote_settings(
    selenium, base_url, default_data, create_experiment, timeout_length
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    review = create_experiment(selenium, home, default_data)
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve(timeout_length)

    for attempt in range(timeout_length):
        try:
            review = SummaryPage(selenium, base_url).wait_for_page_to_load()
            review.timeout_text
        except NoSuchElementException:
            time.sleep(2)
        else:
            assert review.timeout_text, "Timeout text not shown."
            break
    else:
        raise AssertionError("Timeout text was never shown.")


@pytest.mark.run_once
def test_end_experiment_and_approve_end(
    selenium,
    base_url,
    default_data,
    create_experiment,
    perform_kinto_action,
    timeout_length,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    current_experiments = None
    try:
        current_experiments = len(home.tables[0].experiments)
    except TimeoutException:
        current_experiments = 0
    review = create_experiment(selenium, home, default_data)
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve(timeout_length)

    perform_kinto_action(selenium, base_url, "approve")

    selenium.get(base_url)
    # refresh until the experiment shows up
    for attempt in range(timeout_length):
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
    for item in live_experiments.experiments:
        if default_data.public_name in item.text:
            item.click()
            break
    summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
    summary_page.end_experiment()
    summary_page.approve(timeout_length)
    perform_kinto_action(selenium, base_url, "approve")
    # refresh page until kinto updates
    url = default_data.public_name.lower().replace("[", "").replace("]", "")
    for _ in range(timeout_length):
        selenium.get(f"{base_url}/{url}")
        summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
        if "Complete" in summary_page.experiment_status:
            break
        else:
            time.sleep(2)
            selenium.refresh()


@pytest.mark.run_once
def test_end_experiment_and_reject_end(
    selenium,
    base_url,
    default_data,
    create_experiment,
    perform_kinto_action,
    timeout_length,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    current_experiments = None
    try:
        current_experiments = len(home.tables[0].experiments)
    except TimeoutException:
        current_experiments = 0
    review = create_experiment(selenium, home, default_data)
    review.launch_without_preview.click()
    review.request_review.click_launch_checkboxes()
    review.request_review.request_launch_button.click()
    review.approve(timeout_length)

    perform_kinto_action(selenium, base_url, "approve")

    selenium.get(base_url)
    # refresh until the experiment shows up
    for attempt in range(timeout_length):
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
    for item in live_experiments.experiments:
        if default_data.public_name in item.text:
            item.click()
            break
    summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
    summary_page.end_experiment()
    summary_page.approve(timeout_length)
    perform_kinto_action(selenium, base_url, "reject")
    url = default_data.public_name.lower().replace("[", "").replace("]", "")
    # refresh page until kinto updates
    for _ in range(timeout_length):
        selenium.get(f"{base_url}/{url}")
        summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
        try:
            assert summary_page.rejected_text
        except NoSuchElementException:
            time.sleep(2)
            selenium.refresh()
        else:
            break
