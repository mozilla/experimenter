import os

import pytest

from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage


@pytest.mark.nimbus_ui
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


@pytest.mark.nimbus_ui
@pytest.mark.xdist_group(name="group2")
def test_clone_experiment(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.clone()
    summary.wait_for_clone_parent_link_visible()


@pytest.mark.nimbus_ui
@pytest.mark.xdist_group(name="group2")
def test_promote_to_rollout(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.promote_first_branch_to_rollout()
    summary.wait_for_clone_parent_link_visible()


@pytest.mark.nimbus_ui
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
    summary = branches.navigate_to_summary()

    assert summary.branch_screenshot_description == expected_description
    # TODO: Maybe compare uploaded image to example image, but probably
    # good enough for now to assert that an image is displayed
    assert summary.branch_screenshot_image is not None


@pytest.mark.nimbus_ui
def test_create_new_experiment_timeout_remote_settings(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.launch_and_approve()
    summary.wait_for_timeout_alert()
    branches = summary.navigate_to_branches()
    # Fill Metrics page
    metrics = branches.save_and_continue()
    if metrics.primary_outcomes:
        metrics.set_primary_outcomes(values=metrics.primary_outcomes[0])
    assert metrics.primary_outcomes[0] != "", "The primary outcome was not set"
    metrics.set_secondary_outcomes(values=metrics.secondary_outcomes[0])
    for outcome in metrics.secondary_outcomes:
        assert outcome[0] != "", "A secondary outcome was not set"


@pytest.mark.nimbus_ui
def test_every_form_page_can_be_resaved(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    overview = summary.navigate_to_overview()
    branches = overview.save_and_continue()
    metrics = branches.save_and_continue()
    audience = metrics.save_and_continue()
    summary = audience.save_and_continue()
    assert summary.experiment_slug is not None
