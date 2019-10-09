import pytest

from pages.base import Base
from pages.home import Home


@pytest.mark.nondestructive
def test_proposed_start_date_fills_correctly(selenium, base_url, fill_overview):
    """Test proposed start date fills."""
    overview = fill_overview
    assert overview.proposed_start_date == ""
    date = "2011-01-11"
    overview.proposed_start_date = date
    assert overview.proposed_start_date == date


@pytest.mark.nondestructive
def test_proposed_experiment_duration_updates_correctly(
    selenium, base_url, fill_overview
):
    """Test proposed experiment duration fills."""
    overview = fill_overview
    assert overview.proposed_experiment_duration == ""
    duration = "25"
    overview.proposed_experiment_duration = duration
    assert overview.proposed_experiment_duration == duration


@pytest.mark.nondestructive
def test_proposed_enrollment_duration_updates_correctly(
    selenium, base_url, fill_overview
):
    """Test proposed enrolled duration updates."""
    overview = fill_overview
    assert overview.proposed_enrollment_duration == ""
    duration = "50"
    overview.proposed_enrollment_duration = duration
    assert overview.proposed_enrollment_duration == duration


@pytest.mark.nondestructive
def test_population_precentage_updates_correctly(selenium, base_url, fill_overview):
    """Test Population precentage updates."""
    overview = fill_overview
    assert overview.population_precentage == "0.0000"
    precentage = "37.0"
    overview.population_precentage = precentage
    assert overview.population_precentage == f"0{precentage}"


@pytest.mark.nondestructive
def test_firefox_channel_updates_correctly(selenium, base_url, fill_overview):
    """Test selecting a Firefox Channel."""
    overview = fill_overview
    assert overview.firefox_channel == ""
    channel = "Nightly"
    overview.firefox_channel = channel
    assert overview.firefox_channel == channel
