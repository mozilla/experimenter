import datetime

import pytest
from dateutil.parser import parse
from pages.experiment_timeline_and_population import TimelineAndPopulationPage


@pytest.mark.nondestructive
def test_proposed_start_date_fills_correctly(selenium, base_url, fill_overview):
    """Test proposed start date fills."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.proposed_start_date == ""
    date = f"{datetime.datetime.now()}"
    new_date = parse(date)
    today = f"{new_date.date()}"
    timeline_pop_form.proposed_start_date = today
    assert timeline_pop_form.proposed_start_date == today


@pytest.mark.nondestructive
def test_proposed_experiment_duration_updates_correctly(
    selenium, base_url, fill_overview
):
    """Test proposed experiment duration fills."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.proposed_experiment_duration == ""
    duration = "25"
    timeline_pop_form.proposed_experiment_duration = duration
    assert timeline_pop_form.proposed_experiment_duration == duration


@pytest.mark.nondestructive
def test_proposed_enrollment_duration_updates_correctly(
    selenium, base_url, fill_overview
):
    """Test proposed enrolled duration updates."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.proposed_enrollment_duration == ""
    duration = "50"
    timeline_pop_form.proposed_enrollment_duration = duration
    assert timeline_pop_form.proposed_enrollment_duration == duration


@pytest.mark.nondestructive
def test_population_precentage_updates_correctly(selenium, base_url, fill_overview):
    """Test Population precentage updates."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.population_precentage == "0.0000"
    precentage = "37.0"
    timeline_pop_form.population_precentage = precentage
    assert timeline_pop_form.population_precentage == precentage


@pytest.mark.nondestructive
def test_firefox_channel_updates_correctly(selenium, base_url, fill_overview):
    """Test selecting a Firefox Channel."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.firefox_channel == "Firefox Channel"
    channel = "Nightly"
    timeline_pop_form.firefox_channel = channel
    assert timeline_pop_form.firefox_channel == channel


@pytest.mark.nondestructive
def test_firefox_min_version_updates_correctly(selenium, base_url, fill_overview):
    """Test setting a Firefox min version."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.firefox_min_version == "Versions"
    version = "75.0"
    timeline_pop_form.firefox_min_version = version
    assert timeline_pop_form.firefox_min_version == version


@pytest.mark.nondestructive
def test_firefox_max_version_updates_correctly(selenium, base_url, fill_overview):
    """Test setting a Firefox max version."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.firefox_max_version == "Versions"
    version = "78.0"
    timeline_pop_form.firefox_max_version = version
    assert timeline_pop_form.firefox_max_version == version


@pytest.mark.skip
@pytest.mark.nondestructive
def test_platform_selection_updates_correctly(selenium, base_url, fill_overview):
    """Test platform selection updates."""
    timeline_pop_form = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    assert timeline_pop_form.platform == "All Platforms"
    channel = "All Linux"
    timeline_pop_form.platform = channel
    assert timeline_pop_form.platform == channel
