from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.metrics import MetricsPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


class BranchesPage(ExperimenterBase):
    """Experiment Branches Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditBranches")
    _reference_branch_name_locator = (By.CSS_SELECTOR, "#referenceBranch-name")
    _reference_branch_description_locator = (
        By.CSS_SELECTOR,
        "#referenceBranch-description",
    )
    _reference_branch_enable_locator = (
        By.CSS_SELECTOR,
        'label[for="referenceBranch.featureEnabled"]',
    )
    _reference_branch_value_locator = (
        By.CSS_SELECTOR,
        "#referenceBranch-featureValue",
    )
    _treatment_branch_name_locator = (By.CSS_SELECTOR, "#treatmentBranches\\[0\\]-name")
    _treatment_branch_description_locator = (
        By.CSS_SELECTOR,
        "#treatmentBranches\\[0\\]-description",
    )
    _treatment_branch_enable_locator = (
        By.CSS_SELECTOR,
        'label[for="treatmentBranches[0].featureEnabled"]',
    )
    _treatment_branch_value_locator = (
        By.CSS_SELECTOR,
        "#treatmentBranches\\[0\\]-featureValue",
    )
    _remove_branch_locator = (By.CSS_SELECTOR, ".bg-transparent")
    _feature_select_locator = (By.CSS_SELECTOR, '[data-testid="feature-config-select"]')
    _add_screenshot_buttons_locator = (By.CSS_SELECTOR, '[data-testid="add-screenshot"]')
    NEXT_PAGE = MetricsPage
    PAGE_TITLE = "Edit Branches Page"

    @property
    def reference_branch_name(self):
        return self.wait_for_and_find_element(
            self._reference_branch_name_locator, "reference branch name"
        ).text

    @reference_branch_name.setter
    def reference_branch_name(self, text=None):
        self.wait_for_and_find_element(
            self._reference_branch_name_locator, "reference branch name"
        ).send_keys(f"{text}")

    @property
    def reference_branch_description(self):
        return self.wait_for_and_find_element(
            self._reference_branch_description_locator, "reference branch description"
        ).text

    @reference_branch_description.setter
    def reference_branch_description(self, text=None):
        self.wait_for_and_find_element(
            self._reference_branch_description_locator, "reference_branch description"
        ).send_keys(f"{text}")

    @property
    def reference_branch_enabled(self):
        return self.wait_for_and_find_element(
            self._reference_branch_enable_locator, "reference branch enabled"
        )

    @property
    def reference_branch_value(self):
        return self.wait_for_and_find_element(
            self._reference_branch_value_locator, "reference branch value"
        ).text

    @reference_branch_value.setter
    def reference_branch_value(self, text=None):
        self.wait_for_and_find_element(
            self._reference_branch_value_locator, "reference branch value"
        ).send_keys(f"{text}")

    @property
    def treatment_branch_name(self):
        return self.wait_for_and_find_element(
            self._treatment_branch_name_locator, "treatment branch name"
        ).text

    @treatment_branch_name.setter
    def treatment_branch_name(self, text=None):
        self.wait_for_and_find_element(
            self._treatment_branch_name_locator, "treatment branch name"
        ).send_keys(f"{text}")

    @property
    def treatment_branch_description(self):
        return self.wait_for_and_find_element(
            self._treatment_branch_description_locator, "treatment branch description"
        ).text

    @treatment_branch_description.setter
    def treatment_branch_description(self, text=None):
        self.wait_for_and_find_element(
            self._treatment_branch_description_locator, "treatment branch description"
        ).send_keys(f"{text}")

    @property
    def treatment_branch_enabled(self):
        return self.wait_for_and_find_element(
            self._treatment_branch_enable_locator, "treatment branch enabled"
        )

    @property
    def treatment_branch_value(self):
        return self.wait_for_and_find_element(
            self._treatment_branch_value_locator, "treatment branch value"
        ).text

    @treatment_branch_value.setter
    def treatment_branch_value(self, text=None):
        self.wait_for_and_find_element(
            self._treatment_branch_value_locator, "treatment branch value"
        ).send_keys(f"{text}")

    def remove_branch(self):
        self.wait_for_and_find_element(
            self._remove_branch_locator, "remove branch button"
        ).click()

    @property
    def feature_config(self):
        return self.wait_for_and_find_element(
            self._feature_select_locator, "feature config"
        ).text

    @feature_config.setter
    def feature_config(self, feature_config_id):
        el = self.wait_for_and_find_element(
            self._feature_select_locator, "feature_config"
        )
        select = Select(el)
        select.select_by_value(feature_config_id)

    @property
    def add_screenshot_buttons(self):
        return self.wait_for_and_find_elements(
            self._add_screenshot_buttons_locator,
            "branch add screenshot button",
        )

    def screenshot_description_field(self, branch="referenceBranch", screenshot_idx=0):
        selector = (
            f'[data-testid="FormScreenshot"] '
            f'textarea[data-testid="{branch}.screenshots[{screenshot_idx}].description"]'
        )
        return self.wait_for_and_find_element(
            (By.CSS_SELECTOR, selector),
            f"screenshot description field for {branch} screenshot {screenshot_idx}",
        )

    def screenshot_image_field(self, branch="referenceBranch", screenshot_idx=0):
        selector = (
            f'[data-testid="FormScreenshot"] '
            f'input[type="file"]'
            f'[data-testid="{branch}.screenshots[{screenshot_idx}].image"]'
        )
        return self.wait_for_and_find_element(
            (By.CSS_SELECTOR, selector),
            f"screenshot image field for {branch} screenshot {screenshot_idx}",
        )
