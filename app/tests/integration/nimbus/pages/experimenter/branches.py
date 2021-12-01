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
    _remove_branch_locator = (By.CSS_SELECTOR, ".bg-transparent")
    _feature_select_locator = (By.CSS_SELECTOR, '[data-testid="feature-config-select"]')
    _add_screenshot_buttons = (By.CSS_SELECTOR, '[data-testid="add-screenshot"]')
    NEXT_PAGE = MetricsPage
    PAGE_TITLE = "Edit Branches Page"

    @property
    def reference_branch_name(self):
        return self.find_element(*self._reference_branch_name_locator).text

    @reference_branch_name.setter
    def reference_branch_name(self, text=None):
        name = self.find_element(*self._reference_branch_name_locator)
        name.send_keys(f"{text}")

    @property
    def reference_branch_description(self):
        return self.find_element(*self._reference_branch_description_locator).text

    @reference_branch_description.setter
    def reference_branch_description(self, text=None):
        name = self.find_element(*self._reference_branch_description_locator)
        name.send_keys(f"{text}")

    def remove_branch(self):
        el = self.find_element(*self._remove_branch_locator)
        el.click()

    @property
    def feature_config(self):
        return self.find_element(*self._feature_select_locator).text

    @feature_config.setter
    def feature_config(self, feature_config="No Feature Firefox Desktop"):
        el = self.find_element(*self._feature_select_locator)
        select = Select(el)
        select.select_by_visible_text(feature_config)

    @property
    def add_screenshot_buttons(self):
        return self.wait_for_and_find_elements(
            self._add_screenshot_buttons,
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
