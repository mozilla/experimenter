import pytest
from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.pages.remote_settings.dashboard import Dashboard
from nimbus.pages.remote_settings.login import Login


@pytest.mark.run_once
def test_archive_experiment(
    selenium,
    default_data,
    create_experiment,
    archived_tab_url,
    drafts_tab_url,
    experiment_url,
):
    # Archive the experiment
    summary = create_experiment(selenium)
    summary.archive()
    summary.wait_for_archive_label_visible()

    # Check it's archived on the home page
    HomePage(selenium, archived_tab_url).open().find_in_table(
        "Archived", default_data.public_name
    )

    # Unarchive the experiment
    summary = SummaryPage(selenium, experiment_url).open()
    summary.archive()
    summary.wait_for_archive_label_not_visible()

    # Check it's in drafts on the home page
    HomePage(selenium, drafts_tab_url).open().find_in_table(
        "Draft", default_data.public_name
    )


@pytest.mark.run_once
def test_clone_experiment(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.clone()
    summary.wait_for_clone_parent_link_visible()


@pytest.mark.run_once
def test_promote_to_rollout(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary_detail = summary.navigate_to_details()
    summary_detail.promote_first_branch_to_rollout()
    summary_detail.wait_for_clone_parent_link_visible()


@pytest.mark.run_once
def test_takeaways(
    selenium,
    kinto_url,
    kinto_review_url,
    experiment_url,
    create_experiment,
):
    create_experiment(selenium).launch_and_approve()

    Login(selenium, kinto_url).open().login()
    Dashboard(selenium, kinto_review_url).open().approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    Dashboard(selenium, kinto_review_url).open().approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_complete_status()

    expected_summary = "Example takeaways summary text"
    summary.takeaways_edit_button.click()
    summary.takeaways_summary_field = expected_summary
    summary.takeaways_recommendation_radio_button("CHANGE_COURSE").click()
    summary.takeaways_save_button.click()

    assert summary.takeaways_summary_text == expected_summary
    assert summary.takeaways_recommendation_badge_text == "Change course"
