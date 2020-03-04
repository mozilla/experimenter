import pytest

from pages.base import Base
from pages.home import Home
from pages.experiment_design import DesignPage


@pytest.mark.nondestructive
def test_overview_type_changes_correctly(base_url, selenium):
    """Test changing experiment type."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    assert "pref" in experiment.experiment_type
    exp_type = "addon"
    experiment.experiment_type = exp_type
    assert exp_type in experiment.experiment_type


@pytest.mark.nondestructive
def test_overview_engineering_owner_changes_correctly(base_url, selenium):
    """Test changing engineering owner."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    assert experiment.engineering_owner is ""
    new_owner = "uitester"
    experiment.engineering_owner = new_owner
    assert new_owner in experiment.engineering_owner


@pytest.mark.nondestructive
def test_public_name_changes_correctly(base_url, selenium):
    """Test adding a public name."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    assert experiment.public_name is ""
    new_public_name = "uitested exp"
    experiment.public_name = new_public_name
    assert new_public_name in experiment.public_name


@pytest.mark.nondestructive
def test_public_description_changes_correctly(base_url, selenium):
    """Test adding a public description."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    assert experiment.public_description is ""
    new_public_description = "THIS IS A LONG DESCRIPTION..!"
    experiment.public_description = new_public_description
    assert new_public_description in experiment.public_description


@pytest.mark.nondestructive
def test_feature_bugzilla_url_changes_correctly(base_url, selenium):
    """Test adding a bugzilla url."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    assert experiment.feature_bugzilla_url is ""
    new_url = "http://bugzilla.org/1234-new-url"
    experiment.feature_bugzilla_url = new_url
    assert new_url in experiment.feature_bugzilla_url


@pytest.mark.nondestructive
def test_related_work_url_changes_correctly(base_url, selenium):
    """Test adding related work urls."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    assert experiment.related_work_urls is ""
    new_url = "http://someawesomeurl.com"
    experiment.related_work_urls = new_url
    assert new_url in experiment.related_work_urls


@pytest.mark.nondestructive
def test_related_experiments_updates_correctly(base_url, selenium):
    """Test updating related experiments."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    assert experiment.related_experiments == "Nothing selected"
    # Choose some random experiment from the list
    experiment.related_experiments = 1
    assert "Nothing selected" not in experiment.related_work_urls
