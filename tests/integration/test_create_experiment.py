import pytest

from pages.base import Base
from pages.home import Home


@pytest.mark.nondestructive
def test_add_branch(base_url, selenium):
    """Test adding a new branch."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    experiment.fill_name("This is a test")
    experiment.fill_short_description("Testing in here")
    experiment.fill_bugzilla_url("http://bugzilla.com/show_bug.cgi?id=1234")
    exp_population = experiment.save_and_continue__btn()
    exp_population.select_firefox_channel()
    exp_population.select_firefox_min_version
    exp_population.input_firefox_pref_name("robot rock")
    exp_population.select_firefox_pref_type()
    exp_population.select_firefox_pref_branch()
    new_branch = exp_population.create_new_branch()
    assert "Branch 2" in new_branch.branch_number.text

@pytest.mark.nondestructive
def test_remove_branch(base_url, selenium):
    """Test removing a branch."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    experiment.fill_name("This is a test")
    experiment.fill_short_description("Testing in here")
    experiment.fill_bugzilla_url("http://bugzilla.com/show_bug.cgi?id=1234")
    exp_population = experiment.save_and_continue__btn()
    exp_population.select_firefox_channel()
    exp_population.select_firefox_min_version()
    exp_population.input_firefox_pref_name("robot rock")
    exp_population.select_firefox_pref_type()
    exp_population.select_firefox_pref_branch()
    current_branch = exp_population.current_branches
    current_branch[-1].remove_branch()
    branches = exp_population.current_branches
    assert len(branches) == 1
    assert "Control Branch" in branches[-1].branch_number.text


@pytest.mark.nondestructive
def test_duplicate_branch_name(base_url, selenium):
    """Test adding a branch with the same name as the control branch."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    experiment.fill_name("This is a test")
    experiment.fill_short_description("Testing in here")
    experiment.fill_bugzilla_url("http://bugzilla.com/show_bug.cgi?id=1234")
    exp_population = experiment.save_and_continue__btn()
    exp_population.fill_firefox_population_percentage()
    exp_population.select_firefox_channel()
    exp_population.select_firefox_min_version()
    exp_population.input_firefox_pref_name("robot rock")
    exp_population.select_firefox_pref_type()
    exp_population.select_firefox_pref_branch()
    control_branch = exp_population.current_branches[0]
    control_branch.set_branch_name("DUPLICATE BRANCH")
    control_branch.set_branch_description('THIS IS A TEST')
    control_branch.set_branch_value("false")
    extra_branch = exp_population.current_branches[-1]
    extra_branch.set_branch_name("DUPLICATE BRANCH")
    extra_branch.set_branch_description('THIS IS A TEST')
    extra_branch.set_branch_value("false")
    exp_population.click_continue()
    selenium.find_element_by_css_selector("#formset .invalid-feedback")

