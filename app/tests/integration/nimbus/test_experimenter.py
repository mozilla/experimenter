import os

import pytest
from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage


@pytest.mark.run_once
@pytest.mark.xdist_group(name="group2")
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
@pytest.mark.xdist_group(name="group2")
def test_clone_experiment(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.clone()
    summary.wait_for_clone_parent_link_visible()


@pytest.mark.run_once
@pytest.mark.xdist_group(name="group2")
def test_promote_to_rollout(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.promote_first_branch_to_rollout()
    summary.wait_for_clone_parent_link_visible()


@pytest.mark.run_once
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


@pytest.mark.run_once
@pytest.mark.xdist_group(name="group2")
def test_branch_screenshot(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    branches = summary.navigate_to_branches()
    branches.add_screenshot_buttons[0].click()

    image_path = os.path.join(os.getcwd(), "example.jpg")
    branches.screenshot_image_field().send_keys(image_path)

    expected_description = "Example screenshot description text"
    branches.screenshot_description_field().send_keys(expected_description)

    branches.save()
    summary_details = branches.navigate_to_details()

    assert summary_details.branch_screenshot_description == expected_description
    # TODO: Maybe compare uploaded image to example image, but probably
    # good enough for now to assert that an image is displayed
    assert summary_details.branch_screenshot_image is not None
