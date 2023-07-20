import os
from urllib.parse import urljoin

import pytest

from nimbus.pages.experimenter.home import HomePage
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers


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
@pytest.mark.skipif(
    "FIREFOX_DESKTOP" in os.getenv("PYTEST_ARGS"),
    reason="Only run for mobile applications",
)
def test_first_run_release_date(
    base_url,
    selenium,
    kinto_client,
    slugify,
    experiment_name,
    application,
):
    experiment_slug = str(slugify(experiment_name))
    targeting = helpers.load_targeting_configs(app=application)[0]
    data = {
        "hypothesis": "Test Hypothesis",
        "application": application,
        "changelogMessage": "test updates",
        "targetingConfigSlug": targeting,
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "featureConfigIds": [2],
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": "1",
                    "value": "{}",
                },
            ],
        },
        "treatmentBranches": [],
        "firefoxMinVersion": "FIREFOX_120",
        "populationPercent": "100",
        "totalEnrolledClients": 55,
        "isFirstRun": True,
        "proposedReleaseDate": "2023-12-12",
    }
    helpers.create_experiment(
        experiment_slug,
        app=application,
        targeting=targeting,
        data=data,
    )

    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_live_status()

    assert summary.first_run
    assert summary.proposed_release_date == "2023-12-12"


@pytest.mark.nimbus_ui
@pytest.mark.skipif(
    "FIREFOX_DESKTOP" in os.getenv("PYTEST_ARGS"),
    reason="Only run for mobile applications",
)
def test_audience_page_release_date(
    base_url,
    selenium,
    slugify,
    experiment_name,
):
    application = "FENIX"
    experiment_slug = str(slugify(experiment_name))
    targeting = helpers.load_targeting_configs(app=application)[0]
    data = {
        "hypothesis": "Test Hypothesis",
        "application": application,
        "changelogMessage": "test updates",
        "targetingConfigSlug": targeting,
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "featureConfigIds": [2],
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": "1",
                    "value": "{}",
                },
            ],
        },
        "treatmentBranches": [],
        "firefoxMinVersion": "FIREFOX_120",
        "populationPercent": "100",
        "totalEnrolledClients": 55,
        "isFirstRun": True,
        "proposedReleaseDate": "2023-12-12",
    }
    helpers.create_experiment(
        experiment_slug,
        app=application,
        targeting=targeting,
        data=data,
    )
    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()

    audience = summary.navigate_to_audience()
    assert audience.is_first_run
    assert audience.proposed_release_date == "2023-12-12"

    audience.make_first_run()
    summary = audience.save_and_continue()

    assert summary.proposed_release_date == "Not set"


@pytest.mark.nimbus_ui
@pytest.mark.skipif(
    "FIREFOX_DESKTOP" in os.getenv("PYTEST_ARGS"),
    reason="Only run for mobile applications",
)
def test_summary_timeline_release_date(
    base_url,
    selenium,
    kinto_client,
    slugify,
    experiment_name,
):
    application = "FENIX"
    experiment_slug = str(slugify(experiment_name))
    targeting = helpers.load_targeting_configs(app=application)[0]
    data = {
        "hypothesis": "Test Hypothesis",
        "application": application,
        "changelogMessage": "test updates",
        "targetingConfigSlug": targeting,
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "featureConfigIds": [2],
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": "1",
                    "value": "{}",
                },
            ],
        },
        "treatmentBranches": [],
        "firefoxMinVersion": "FIREFOX_120",
        "populationPercent": "100",
        "totalEnrolledClients": 55,
        "isFirstRun": True,
        "proposedReleaseDate": "2023-12-12",
    }
    helpers.create_experiment(
        experiment_slug,
        app=application,
        targeting=targeting,
        data=data,
    )

    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, urljoin(base_url, experiment_slug)).open()
    summary.wait_for_live_status()

    summary.wait_for_timeline_visible()
    summary.wait_for_release_date()


@pytest.mark.nimbus_ui
@pytest.mark.skipif(
    ("FOCUS_IOS" or "FIREFOX_IOS" or "FENIX" or "FOCUS_ANDROID")
    in os.getenv("PYTEST_ARGS"),
    reason="Only run for desktop",
)
def test_summary_release_date_not_visible(
    selenium,
    kinto_client,
    create_experiment,
    experiment_url,
):
    summary = create_experiment(selenium)
    summary.launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()

    summary.wait_for_timeline_visible()
    timeline_release_date = summary.wait_until_timeline_release_date_not_found()
    assert not timeline_release_date
    audience_release_date = summary.wait_until_audience_section_release_date_not_found()
    assert not audience_release_date


@pytest.mark.nimbus_ui
@pytest.mark.skipif(
    ("FOCUS_IOS" or "FIREFOX_IOS" or "FENIX" or "FOCUS_ANDROID")
    in os.getenv("PYTEST_ARGS"),
    reason="Only run for desktop",
)
def test_audience_page_release_date_not_visible(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    audience = summary.navigate_to_audience()

    release_date = audience.wait_until_release_date_not_found()
    assert not release_date
    first_run = audience.wait_until_first_run_not_found()
    assert not first_run
