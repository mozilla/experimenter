from pathlib import Path

import pytest

from nimbus.models.base_dataclass import (
    BaseExperimentApplications,
)
from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage

MOBILE_APPS = [
    BaseExperimentApplications.FIREFOX_FENIX.value,
    BaseExperimentApplications.FIREFOX_IOS.value,
    BaseExperimentApplications.FOCUS_ANDROID.value,
    BaseExperimentApplications.FOCUS_IOS.value,
]


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

    image_path = Path.cwd() / "example.jpg"
    branches.screenshot_image_field().send_keys(str(image_path))

    expected_description = "Example screenshot description text"
    branches.screenshot_description_field().send_keys(expected_description)

    branches.save()
    summary = branches.navigate_to_summary()

    assert summary.branch_screenshot_description == expected_description
    # TODO: Maybe compare uploaded image to example image, but probably
    # good enough for now to assert that an image is displayed
    assert summary.branch_screenshot_image is not None


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


@pytest.mark.nimbus_ui
def test_first_run_release_date_visible_for_mobile(
    selenium,
    kinto_client,
    application,
    create_experiment,
    experiment_url,
):
    if application not in MOBILE_APPS:
        pytest.skip(f"Skipping for {application}")

    summary = create_experiment(selenium)

    audience = summary.navigate_to_audience()
    audience.make_first_run()
    audience.proposed_release_date = "2023-12-12"

    assert audience.is_first_run
    assert audience.proposed_release_date == "2023-12-12"

    summary = audience.save_and_continue()

    assert summary.proposed_release_date == "2023-12-12"

    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()

    assert summary.first_run
    assert summary.proposed_release_date == "2023-12-12"


@pytest.mark.nimbus_ui
def test_first_run_release_date_not_visible_for_non_mobile(
    selenium,
    kinto_client,
    application,
    create_experiment,
    experiment_url,
):
    if application in MOBILE_APPS:
        pytest.skip(f"Skipping for {application}")

    summary = create_experiment(selenium)

    audience = summary.navigate_to_audience()

    audience.wait_until_release_date_not_found()
    audience.wait_until_first_run_not_found()

    summary = audience.navigate_to_summary()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()

    summary.wait_for_timeline_visible()
    summary.wait_until_timeline_release_date_not_found()
    summary.wait_until_audience_release_date_not_found()
    summary.wait_until_audience_first_run_not_found()
