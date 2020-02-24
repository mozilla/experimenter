"""Representaion of the Experiment Design Page."""

import random
import string

from selenium.webdriver.common.by import By
from pypom import Region

from pages.base import Base


class DesignPage(Base):

    _add_branch_btn_locator = (By.CSS_SELECTOR, "#add-branch-button")
    _branch_form_root_locator = (By.CSS_SELECTOR, "#control-branch-group")
    _continue_btn_locator = (By.CSS_SELECTOR, "#save-continue")
    _firefox_pref_name_locator = (By.CSS_SELECTOR, "#id_pref_name")
    _firefox_pref_type_locator = (By.CSS_SELECTOR, "#id_pref_type")
    _firefox_pref_branch_locator = (By.CSS_SELECTOR, "#id_pref_branch")
    _new_branch_locator = (
        By.CSS_SELECTOR,
        "#formset > div:nth-child(5) > div:nth-child(3) > div:nth-child(1) > h4:nth-child(1)",
    )
    _page_wait_locator = (By.CSS_SELECTOR, "body.page-edit-variants")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(
                *self._firefox_pref_name_locator).is_displayed()
            )
        return self

    def create_new_branch(self):
        """Creates a new branch."""
        num_of_branches = len(self.current_branches) + 1
        self.find_element(*self._add_branch_btn_locator).click()
        els = self.find_elements(*self._branch_form_root_locator)
        return self.BranchRegion(self, els[-1], count=num_of_branches)

    @property
    def current_branches(self):
        """Returns list of current branches."""
        els = self.find_elements(*self._branch_form_root_locator)
        branches = [
            self.BranchRegion(self, root=el, count=count) for count, el in enumerate(els)
        ]
        for count, item in enumerate(branches):
            if not item.is_displayed:
                del branches[count]
        return branches

    def input_firefox_pref_name(self, text=None):
        element = self.find_element(*self._firefox_pref_name_locator)
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        element.send_keys(f"{text}-{random_chars}")
        return

    def select_firefox_pref_type(self):
        self.find_element(*self._firefox_pref_type_locator).click()
        return

    def select_firefox_pref_branch(self):
        self.find_element(*self._firefox_pref_branch_locator).click()
        return

    def click_continue(self):
        self.find_element(*self._continue_btn_locator).click()
        return

    class BranchRegion(Region):
        def __init__(self, page, root=None, count=None, **kwargs):
            super().__init__(page=page, root=root, **kwargs)
            self.number = count

        _remove_branch_btn_locator = (By.CSS_SELECTOR, "#remove-branch-button")
        _new_branch_locator = (By.CSS_SELECTOR, "div > div > h4")

        @property
        def is_displayed(self):
            """Check if a branch is displayed."""
            if self.root.get_attribute("data-formset-form-deleted") is not None:
                return False
            return True

        def remove_branch(self):
            self.find_element(*self._remove_branch_btn_locator).click()
            return

        @property
        def branch_number(self):
            return self.find_element(*self._new_branch_locator)

        def set_branch_name(self, text=None):
            locator = (By.ID, f"variants-{self.number}-name")
            element = self.find_element(*locator)
            element.send_keys(text)
            return

        def set_branch_description(self, text=None):
            locator = (By.ID, f"variants-{self.number}-description")
            element = self.find_element(*locator)
            element.send_keys(text)
            return

        def set_branch_value(self, text=None):
            locator = (By.ID, f"variants-{self.number}-value")
            element = self.find_element(*locator)
            element.send_keys(text)
            return
