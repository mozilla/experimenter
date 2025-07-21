from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.metrics import MetricsPage


class BranchesPage(ExperimenterBase):
    """Experiment Branches Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditBranches")
    _reference_branch_name_locator = (By.CSS_SELECTOR, "#referenceBranch-name")
    _reference_branch_description_locator = (
        By.CSS_SELECTOR,
        "#referenceBranch-description",
    )
    _reference_branch_value_locator = (
        By.CSS_SELECTOR,
        "#referenceBranch\\.featureValues\\[0\\]\\.value",
    )
    _treatment_branch_name_locator = (By.CSS_SELECTOR, "#treatmentBranches\\[0\\]-name")
    _treatment_branch_description_locator = (
        By.CSS_SELECTOR,
        "#treatmentBranches\\[0\\]-description",
    )
    _treatment_branch_value_locator = (
        By.CSS_SELECTOR,
        "#treatmentBranches\\[0\\]\\.featureValues\\[0\\]\\.value",
    )
    _remove_branch_locator = (By.CSS_SELECTOR, ".bg-transparent")
    _feature_select_locator = (By.CSS_SELECTOR, '[aria-label="Features"]')
    _add_screenshot_buttons_locator = (By.CSS_SELECTOR, '[data-testid="add-screenshot"]')
    _rollout_checkbox_locator = (By.CSS_SELECTOR, '[data-testid="is-rollout-checkbox"]')
    NEXT_PAGE = MetricsPage
    PAGE_TITLE = "Edit Branches Page"

    def _feature_config_id_locator(self, feature_config_id: int):
        return (
            By.CSS_SELECTOR,
            f'.react-select__option[data-feature-config-id="{feature_config_id}"]',
        )

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
            *self._reference_branch_description_locator, "reference branch description"
        ).text

    @reference_branch_description.setter
    def reference_branch_description(self, text=None):
        self.wait_for_and_find_element(
            *self._reference_branch_description_locator, "reference_branch description"
        ).send_keys(f"{text}")

    @property
    def reference_branch_value(self):
        return self._get_feature_value(
            self.wait_for_and_find_element(
                *self._reference_branch_value_locator, "reference branch value"
            )
        )

    @reference_branch_value.setter
    def reference_branch_value(self, text):
        self._set_feature_value(
            self.wait_for_and_find_element(
                *self._reference_branch_value_locator, "reference branch value"
            ),
            text,
        )

    @property
    def treatment_branch_name(self):
        return self.wait_for_and_find_element(
            *self._treatment_branch_name_locator, "treatment branch name"
        ).text

    @treatment_branch_name.setter
    def treatment_branch_name(self, text=None):
        self.wait_for_and_find_element(
            *self._treatment_branch_name_locator, "treatment branch name"
        ).send_keys(f"{text}")

    @property
    def treatment_branch_description(self):
        return self.wait_for_and_find_element(
            *self._treatment_branch_description_locator, "treatment branch description"
        ).text

    @treatment_branch_description.setter
    def treatment_branch_description(self, text=None):
        self.wait_for_and_find_element(
            *self._treatment_branch_description_locator, "treatment branch description"
        ).send_keys(f"{text}")

    @property
    def treatment_branch_value(self):
        return self._get_feature_value(
            self.wait_for_and_find_element(
                *self._treatment_branch_value_locator, "treatment branch value"
            )
        )

    @treatment_branch_value.setter
    def treatment_branch_value(self, text):
        self._set_feature_value(
            self.wait_for_and_find_element(
                *self._treatment_branch_value_locator, "treatment branch value"
            ),
            text,
        )

    def remove_branch(self):
        self.wait_for_and_find_element(
            *self._remove_branch_locator, "remove branch button"
        ).click()

    @property
    def feature_config(self):
        return self.wait_for_and_find_element(
            *self._feature_select_locator, "feature configs"
        ).text

    @feature_config.setter
    def feature_config(self, feature_config_id):
        el = self.wait_for_and_find_element(
            *self._feature_select_locator, "feature configs"
        )

        el.click()  # Open the drop-down

        self.wait_for_and_find_element(
            *self._feature_config_id_locator(feature_config_id),
            f"feature config {feature_config_id}",
        ).click()

    @property
    def is_rollout(self):
        return self.wait_for_and_find_element(
            *self._rollout_checkbox_locator, "is rollout"
        )

    def make_rollout(self):
        self.wait_for_and_find_element(
            *self._rollout_checkbox_locator, "is_rollout"
        ).click()

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
        line = editor_element.find_elements(By.CSS_SELECTOR, ".cm-line")[-1]
        line.click()

        actions = ActionChains(self.driver)
        actions.send_keys(text)
        actions.perform()

        # Click outside the editor, which causes the form data to update.
        self.find_element(By.CSS_SELECTOR, "#PageEditBranches").click()

    def screenshot_description_field(self, branch="referenceBranch", screenshot_idx=0):
        selector = (
            f'[data-testid="FormScreenshot"] '
            f'textarea[data-testid="{branch}.screenshots[{screenshot_idx}].description"]'
        )
        return self.wait_for_and_find_element(
            By.CSS_SELECTOR,
            selector,
            f"screenshot description field for {branch} screenshot {screenshot_idx}",
        )

    def screenshot_image_field(self, branch="referenceBranch", screenshot_idx=0):
        selector = (
            f'[data-testid="FormScreenshot"] '
            f'input[type="file"]'
            f'[data-testid="{branch}.screenshots[{screenshot_idx}].image"]'
        )
        return self.wait_for_and_find_element(
            By.CSS_SELECTOR,
            selector,
            f"screenshot image field for {branch} screenshot {screenshot_idx}",
        )
