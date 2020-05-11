"""Representaion of the Experiment Design Page."""

import random
import string

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from pypom import Region

from pages.base import Base


class DesignPage(Base):

    URL_TEMPLATE = "{experiment_url}edit-design"

    _add_branch_btn_locator = (By.CSS_SELECTOR, "#add-branch-button")
    _branch_form_root_locator = (By.CSS_SELECTOR, "#control-branch-group")
    _continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-btn")
    _firefox_pref_name_locator = (By.CSS_SELECTOR, "#id_pref_name")
    _firefox_pref_type_locator = (By.CSS_SELECTOR, "#id_pref_type")
    _firefox_pref_branch_locator = (By.CSS_SELECTOR, "#id_pref_branch")
    _multipref_radio_btn_locator = (By.CSS_SELECTOR, "#is_multi_pref-true")
    _new_branch_locator = (By.CSS_SELECTOR, "#add-branch-button")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._add_branch_btn_locator).is_displayed()
        )
        return self

    def enable_multipref(self):
        element = self.find_element(*self._multipref_radio_btn_locator)
        element.click()
        return self.wait_for_page_to_load()

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

    def select_firefox_pref_type(self, item):
        element = self.find_element(*self._firefox_pref_type_locator)
        selector = Select(element)
        selector.select_by_visible_text(f"{item}")
        return

    def select_firefox_pref_branch(self, item):
        element = self.find_element(*self._firefox_pref_branch_locator)
        selector = Select(element)
        selector.select_by_visible_text(f"{item}")
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

        def set_branch_ratio(self, num=None):
            locator = (By.ID, f"variants-{self.number}-ratio")
            element = self.find_element(*locator)
            element.send_keys(num)

        @property
        def branch_name(self):
            locator = (By.ID, f"variants-{self.number}-name")
            return self.find_element(*locator).text

        @branch_name.setter
        def branch_name(self, text=None):
            locator = (By.ID, f"variants-{self.number}-name")
            element = self.find_element(*locator)
            element.send_keys(text)

        @property
        def branch_description(self):
            locator = (By.ID, f"variants-{self.number}-description")
            return self.find_element(*locator).text

        @branch_description.setter
        def branch_description(self, text=None):
            locator = (By.ID, f"variants-{self.number}-description")
            element = self.find_element(*locator)
            element.send_keys(text)
            return

        @property
        def branch_value(self):
            locator = (By.ID, f"variants-{self.number}-value")
            return self.find_element(*locator).text

        @branch_value.setter
        def branch_value(self, text=None):
            locator = (By.ID, f"variants-{self.number}-value")
            element = self.find_element(*locator)
            element.send_keys(text)
            return

        def set_pref_branch(self, item):
            locator = (By.ID, f"pref-branch-{self.number}-0")
            element = self.find_element(*locator)
            selector = Select(element)
            selector.select_by_visible_text(f"{item}")

        def set_pref_type(self, item):
            locator = (By.ID, f"pref-type-{self.number}-0")
            element = self.find_element(*locator)
            selector = Select(element)
            selector.select_by_visible_text(f"{item}")

        @property
        def pref_name(self):
            locator = (By.CSS_SELECTOR, f"#pref-key-{self.number}-0")
            return self.find_element(*locator).text

        @pref_name.setter
        def pref_name(self, text=None):
            locator = (By.CSS_SELECTOR, f"#pref-key-{self.number}-0")
            element = self.find_element(*locator)
            element.send_keys(text)

        @property
        def pref_value(self):
            locator = (By.CSS_SELECTOR, f"#pref-value-{self.number}-0")
            return self.find_element(*locator).text

        @pref_value.setter
        def pref_value(self, text=None):
            locator = (By.CSS_SELECTOR, f"#pref-value-{self.number}-0")
            element = self.find_element(*locator)
            element.send_keys(text)
