import pytest

from pages.base import Base


@pytest.mark.nondestructive
def test_owned_experiments_page_loads(base_url, selenium):
    """Test Owned Experiments link opens correct page."""
    selenium.get(base_url)
    page = Base(selenium, base_url)
    experiments = page.header.click_owned_experiments()
    assert "Experiments" in experiments.title


@pytest.mark.nondestructive
def test_subscribed_experiments_page_loads(base_url, selenium):
    """Test Subscribed Experiments link opens correct page."""
    selenium.get(base_url)
    page = Base(selenium, base_url)
    experiments = page.header.click_subscribed_experiments()
    assert "Subscribed Experiments" in experiments.title
