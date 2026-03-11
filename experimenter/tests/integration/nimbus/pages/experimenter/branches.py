from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.metrics import MetricsPage


class BranchesPage(ExperimenterBase):
    """Experiment Branches Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#branches-form")
    _reference_branch_name_locator = (By.CSS_SELECTOR, "#referenceBranch-name")
    _reference_branch_description_locator = (
        By.CSS_SELECTOR,
        "#id_branches-0-description",
    )
    _branch_value_locator = (
        By.CSS_SELECTOR,
        "#branches-form #branches .feature-value-editor .cm-activeLine",
    )
    _treatment_branch_name_locator = (By.CSS_SELECTOR, "#id_branches-0-name")
    _treatment_branch_description_locator = (
        By.CSS_SELECTOR,
        "#id_branches-1-description",
    )
    _remove_branch_locator = (By.CSS_SELECTOR, ".bg-transparent")
    _feature_select_locator = (By.CSS_SELECTOR, "#branches-form .dropdown")
    _feature_search_locator = (By.CSS_SELECTOR, ".bs-searchbox > input:nth-child(1)")
    _add_screenshot_buttons_locator = (By.CSS_SELECTOR, "#add-screenshot-button")
    _rollout_checkbox_locator = (By.CSS_SELECTOR, '[data-testid="is-rollout-checkbox"]')
    _feature_config_id_locator = (By.CSS_SELECTOR, "#id_feature_configs > option")
    NEXT_PAGE = MetricsPage
    PAGE_TITLE = "Edit Branches Page"

    @property
    def reference_branch_description(self):
        return self.get_input(self._reference_branch_description_locator).text

    @reference_branch_description.setter
    def reference_branch_description(self, text=None):
        el = self.get_input(self._reference_branch_description_locator)
        el.send_keys(f"{text}")

    @property
    def reference_branch_value(self):
        elements = self.wait_for_and_find_elements(
            *self._branch_value_locator, "reference branch value"
        )
        return self._get_feature_value(elements[0])

    @reference_branch_value.setter
    def reference_branch_value(self, text):
        elements = self.wait_for_and_find_elements(
            *self._branch_value_locator, "reference branch value"
        )
        self._set_feature_value(elements[0], text)

    @property
    def treatment_branch_description(self):
        return self.get_input(self._treatment_branch_description_locator).text

    @treatment_branch_description.setter
    def treatment_branch_description(self, text=None):
        el = self.get_input(self._treatment_branch_description_locator)
        el.send_keys(f"{text}")

    @property
    def treatment_branch_value(self):
        elements = self.wait_for_and_find_elements(
            *self._branch_value_locator, "treatment branch value"
        )
        return self._get_feature_value(elements[-1])

    @treatment_branch_value.setter
    def treatment_branch_value(self, text):
        elements = self.wait_for_and_find_elements(
            *self._branch_value_locator, "treatment branch value"
        )
        self._set_feature_value(elements[-1], text)

    def remove_branch(self):
        self.click_element(self._remove_branch_locator)

    @property
    def feature_config(self):
        return self.wait_for_and_find_element(
            *self._feature_select_locator, "feature configs"
        ).text

    @feature_config.setter
    def feature_config(self, feature_config_id):
        self.set_bootstrap_select(
            self._feature_select_locator,
            self._feature_search_locator,
            [feature_config_id],
        )

    @property
    def is_rollout(self):
        return self.wait_for_and_find_element(
            *self._rollout_checkbox_locator, "is rollout"
        )

    def make_rollout(self):
        self.click_element(self._rollout_checkbox_locator)

    @property
    def add_screenshot_buttons(self):
        return self.wait_for_and_find_elements(
            *self._add_screenshot_buttons_locator,
            "branch add screenshot button",
        )

    def _get_feature_value(self, editor_element):
        return "\n".join(
            line.text
            for line in editor_element.find_elements(By.CSS_SELECTOR, ".cm-line")
        )

    def _set_feature_value(self, editor_element, text):
        editor_element.click()
        actions = ActionChains(self.driver)
        actions.double_click(editor_element)
        actions.send_keys(text)
        actions.perform()

        # Click outside the editor, which causes the form data to update.
        self.find_element(*self._page_wait_locator).click()

    def screenshot_description_field(self, branch="referenceBranch", screenshot_idx=0):
        selector = (
            f"#id_branches-{screenshot_idx}-screenshots-{screenshot_idx}-description"
        )
        return self.wait_for_and_find_element(
            By.CSS_SELECTOR,
            selector,
            f"screenshot description field for {screenshot_idx}",
        )

    def screenshot_image_field(self, branch="referenceBranch", screenshot_idx=0):
        selector = f"#id_branches-{screenshot_idx}-screenshots-{screenshot_idx}-image"
        return self.wait_for_and_find_element(
            By.CSS_SELECTOR,
            selector,
            f"screenshot image field for {screenshot_idx}",
        )
