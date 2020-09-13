"""Representaion of the Experiment Design Page."""

import random
import string

from pages.base import Base
from pypom import Region
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


class DesignPage(Base):

    URL_TEMPLATE = "{experiment_url}edit-design"
    _page_wait_locator = (By.CSS_SELECTOR, ".page-edit-design")

    _add_branch_btn_locator = (By.CSS_SELECTOR, "#add-branch-button")
    _addon_rollout_button_locator = (By.CSS_SELECTOR, "#rollout_type-addon")
    _branch_form_root_locator = (By.CSS_SELECTOR, "#control-branch-group")
    _continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-btn")
    _design_textarea_locator = (By.CSS_SELECTOR, "#id_design")
    _firefox_pref_name_locator = (By.CSS_SELECTOR, "#id_pref_name")
    _firefox_pref_type_locator = (By.CSS_SELECTOR, "#id_pref_type")
    _firefox_pref_branch_locator = (By.CSS_SELECTOR, "#id_pref_branch")
    _multipref_radio_btn_locator = (By.CSS_SELECTOR, "#is_multi_pref-true")
    _new_branch_locator = (By.CSS_SELECTOR, "#add-branch-button")
    _signed_addon_url_locator = (By.CSS_SELECTOR, "#signed-addon-url")
    _single_addon_button_locator = (By.CSS_SELECTOR, "#is_branched_addon-false")
    _multi_addon_button_locator = (By.CSS_SELECTOR, "#is_branched_addon-true")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    def enable_multipref(self):
        element = self.find_element(*self._multipref_radio_btn_locator)
        element.click()
        return self.wait_for_page_to_load()

    def enable_single_addon(self):
        element = self.find_element(*self._single_addon_button_locator)
        element.click()

    def enable_multi_addon(self):
        element = self.find_element(*self._multi_addon_button_locator)
        element.click()

    def enable_addon_rollout(self):
        element = self.find_element(*self._addon_rollout_button_locator)
        element.click()

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

    @property
    def design_details(self):
        element = self.find_element(*self._design_textarea_locator)
        return element.text

    @design_details.setter
    def design_details(self, text=None):
        element = self.find_element(*self._design_textarea_locator)
        element.send_keys(text)

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

    @property
    def signed_addon_url(self):
        element = self.find_element(*self._signed_addon_url_locator)
        return element.text

    @signed_addon_url.setter
    def signed_addon_url(self, text=None):
        try:
            assert self.signed_addon_url == "", "Form field not empty"
        except AssertionError:
            return
        else:
            element = self.find_element(*self._signed_addon_url_locator)
            element.send_keys(text)

    def click_continue(self):
        self.find_element(*self._continue_btn_locator).click()
        return

    @property
    def rollout_prefs(self):
        return self.RolloutPrefs(self)

    class RolloutPrefs(Region):
        _addon_url_locator = (By.CSS_SELECTOR, "#id_addon_release_url")
        _pref_branch_locator = (By.CSS_SELECTOR, "#pref-branch-undefined-0")
        _pref_type_locator = (By.CSS_SELECTOR, "#pref-type-undefined-0")
        _pref_name_locator = (By.CSS_SELECTOR, "#pref-key-undefined-0")
        _pref_value_locator = (By.CSS_SELECTOR, "#pref-value-undefined-0")

        @property
        def pref_branch(self):
            return self.selenium.find_element(*self._pref_branch_locator).text

        @pref_branch.setter
        def pref_branch(self, item):
            element = self.selenium.find_element(*self._pref_branch_locator)
            selector = Select(element)
            selector.select_by_visible_text(f"{item}")

        @property
        def pref_type(self):
            return self.selenium.find_element(*self._pref_type_locator).text

        @pref_type.setter
        def pref_type(self, item):
            element = self.selenium.find_element(*self._pref_type_locator)
            selector = Select(element)
            selector.select_by_visible_text(f"{item}")

        @property
        def pref_name(self):
            return self.selenium.find_element(*self._pref_name_locator).text

        @pref_name.setter
        def pref_name(self, text=None):
            element = self.selenium.find_element(*self._pref_name_locator)
            element.send_keys(text)

        @property
        def pref_value(self):
            return self.selenium.find_element(*self._pref_value_locator).text

        @pref_value.setter
        def pref_value(self, text=None):
            element = self.selenium.find_element(*self._pref_value_locator)
            element.send_keys(text)

        @property
        def addon_url(self):
            return self.selenium.find_element(*self._addon_url_locator).text

        @addon_url.setter
        def addon_url(self, text=None):
            element = self.selenium.find_element(*self._addon_url_locator)
            element.send_keys(text)

    class BranchRegion(Region):
        def __init__(self, page, root=None, count=None, **kwargs):
            super().__init__(page=page, root=root, **kwargs)
            self.number = count

        _add_pref_btn_locator = (By.CSS_SELECTOR, "#add-pref-button")
        _remove_branch_btn_locator = (By.CSS_SELECTOR, "#remove-branch-button")
        _new_branch_locator = (By.CSS_SELECTOR, "div > div > h4")
        _pref_section_locator = (By.CSS_SELECTOR, "#control-branch-group-pref")

        @property
        def is_displayed(self):
            """Check if a branch is displayed."""
            if self.root.get_attribute("data-formset-form-deleted") is not None:
                return False
            return True

        @property
        def add_pref_button(self):
            return self.find_element(*self._add_pref_btn_locator)

        def prefs(self, branch):
            # Create PrefsRegion objects for each branch and each pref seen
            els = self.find_elements(*self._pref_section_locator)

            _prefs = []
            for count, el in enumerate(els):
                _prefs.append(
                    self.PrefsRegion(self, root=el, count=count, branch_number=branch)
                )
            return _prefs

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

        @property
        def signed_addon_url(self):
            locator = (By.ID, f"variants-{self.number}-addon_release_url")
            return self.find_element(*locator).text

        @signed_addon_url.setter
        def signed_addon_url(self, text=None):
            locator = (By.ID, f"variants-{self.number}-addon_release_url")
            element = self.find_element(*locator)
            element.send_keys(text)
            return

        class PrefsRegion(Region):
            def __init__(self, page, root=None, count=None, branch_number=None, **kwargs):
                super().__init__(page=page, root=root, **kwargs)
                self.pref_number = count
                self.branch_number = branch_number

            @property
            def pref_branch(self):
                locator = (
                    By.CSS_SELECTOR,
                    f"#pref-branch-{self.branch_number}-{self.pref_number}",
                )
                return self.selenium.find_element(*locator).text

            @pref_branch.setter
            def pref_branch(self, item):
                locator = (
                    By.CSS_SELECTOR,
                    f"#pref-branch-{self.branch_number}-{self.pref_number}",
                )
                element = self.selenium.find_element(*locator)
                selector = Select(element)
                selector.select_by_visible_text(f"{item}")

            @property
            def pref_type(self):
                locator = (By.ID, f"pref-type-{self.branch_number}-{self.pref_number}")
                return self.selenium.find_element(*locator).text

            @pref_type.setter
            def pref_type(self, item):
                locator = (By.ID, f"pref-type-{self.branch_number}-{self.pref_number}")
                element = self.selenium.find_element(*locator)
                selector = Select(element)
                selector.select_by_visible_text(f"{item}")

            @property
            def pref_name(self):
                locator = (
                    By.CSS_SELECTOR,
                    f"#pref-key-{self.branch_number}-{self.pref_number}",
                )
                return self.selenium.find_element(*locator).text

            @pref_name.setter
            def pref_name(self, text=None):
                locator = (
                    By.CSS_SELECTOR,
                    f"#pref-key-{self.branch_number}-{self.pref_number}",
                )
                element = self.selenium.find_element(*locator)
                element.send_keys(text)

            @property
            def pref_value(self):
                locator = (
                    By.CSS_SELECTOR,
                    f"#pref-value-{self.branch_number}-{self.pref_number}",
                )
                return self.selenium.find_element(*locator).text

            @pref_value.setter
            def pref_value(self, text=None):
                locator = (
                    By.CSS_SELECTOR,
                    f"#pref-value-{self.branch_number}-{self.pref_number}",
                )
                element = self.selenium.find_element(*locator)
                actions = ActionChains(self.selenium)
                actions.double_click(element).perform()
                element.send_keys(text)
