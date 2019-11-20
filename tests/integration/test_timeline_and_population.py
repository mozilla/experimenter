import datetime

from dateutil.parser import parse
import pytest

from pages.base import Base
from pages.home import Home


@pytest.fixture
def setup_form(selenium, fill_overview):
    overview = fill_overview
    # Setup form since we have to save and come back
    date = f"{datetime.datetime.now()}"
    date = parse(date)
    overview.proposed_start_date = f"{date.date()}"
    overview.firefox_channel = "Nightly"
    overview.proposed_enrollment_duration = "50"
    overview.proposed_experiment_duration = "55"
    overview.population_precentage = "37.0"
    return overview


@pytest.mark.nondestructive
def test_proposed_start_date_fills_correctly(selenium, base_url, fill_overview):
    """Test proposed start date fills."""
    overview = fill_overview
    assert overview.proposed_start_date == ""
    date = f"{datetime.datetime.now()}"
    new_date = parse(date)
    today = f"{new_date.date()}"
    overview.proposed_start_date = today
    assert overview.proposed_start_date == today


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


@pytest.mark.nondestructive
def test_firefox_min_version_updates_correctly(selenium, base_url, setup_form):
    """Test setting a Firefox min version."""
    form = setup_form
    assert form.firefox_min_version == ""
    form.firefox_max_version = "80.0"
    version = "65.0"
    form.firefox_min_version = version
    form.save_and_continue()
    selenium.back()
    assert form.firefox_min_version == version


@pytest.mark.nondestructive
def test_firefox_max_version_updates_correctly(selenium, base_url, setup_form):
    """Test setting a Firefox max version."""
    form = setup_form
    form.firefox_min_version = "65.0"
    assert form.firefox_max_version == ""
    version = "80.0"
    form.firefox_max_version = version
    form.save_and_continue()
    selenium.back()
    assert form.firefox_max_version == version


@pytest.mark.nondestructive
def test_locales_update_correctly(selenium, base_url, fill_overview):
    """Test locale updates correctly."""
    form = fill_overview
    assert "All locales" in form.locale
    new_locale = "Bengali"
    form.locale = new_locale
    assert new_locale in form.locale


@pytest.mark.nondestructive
def test_platform_selection_updates_correctly(selenium, base_url, fill_overview):
    """Test platform selection updates."""
    form = fill_overview
    assert form.platform == "All Platforms"
    channel = "All Linux"
    form.platform = channel
    assert form.platform == channel