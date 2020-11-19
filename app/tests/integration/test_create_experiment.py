import pytest
from pages.experiment_design import DesignPage


@pytest.mark.skip(reason="superceded by e2e tests")
@pytest.mark.nondestructive
def test_add_branch(base_url, selenium, ds_issue_host, fill_overview):
    """Test adding a new branch."""
    exp_design = DesignPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    exp_design.input_firefox_pref_name("robot rock")
    exp_design.select_firefox_pref_type("boolean")
    exp_design.select_firefox_pref_branch("default")
    new_branch = exp_design.create_new_branch()
    assert "Branch 2" in new_branch.branch_number.text


@pytest.mark.skip(reason="superceded by e2e tests")
@pytest.mark.nondestructive
def test_remove_branch(base_url, selenium, fill_overview):
    """Test removing a branch."""
    exp_design = DesignPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    exp_design.input_firefox_pref_name("robot rock")
    exp_design.select_firefox_pref_type("boolean")
    exp_design.select_firefox_pref_branch("default")
    current_branch = exp_design.current_branches
    current_branch[-1].remove_branch()
    branches = exp_design.current_branches
    assert len(branches) == 1
    assert "Control Branch" in branches[-1].branch_number.text


@pytest.mark.skip(reason="superceded by e2e tests")
@pytest.mark.nondestructive
def test_duplicate_branch_name(base_url, selenium, ds_issue_host, fill_overview):
    """Test adding a branch with the same name as the control branch."""
    exp_design = DesignPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    exp_design.input_firefox_pref_name("robot rock")
    exp_design.select_firefox_pref_type("boolean")
    exp_design.select_firefox_pref_branch("default")
    control_branch = exp_design.current_branches[0]
    control_branch.branch_name = "DUPLICATE BRANCH"
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_value = "false"
    extra_branch = exp_design.current_branches[-1]
    extra_branch.branch_name = "DUPLICATE BRANCH"
    extra_branch.branch_description = "THIS IS A TEST"
    extra_branch.branch_value = "false"
    exp_design.save_and_continue()
    selenium.find_element_by_css_selector("#design-form .invalid-feedback")
