from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.rollouts.form_base import FormBase


class FeaturesSection(FormBase):
    """Features section of the rollout detail page."""

    PAGE_TITLE = "Rollout Features"
    CARD_ID = "rollout-features"

    _rollout_experience_locator = (By.ID, "id_rollout_experience")
    _feature_configs_button_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_feature_configs']",
    )
    _feature_configs_search_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_feature_configs'] + .dropdown-menu input",
    )
    _warn_feature_schema_locator = (By.ID, "id_warn_feature_schema")
    _prevent_pref_conflicts_locator = (By.ID, "id_prevent_pref_conflicts")
    _is_firefox_labs_opt_in_locator = (By.ID, "id_is_firefox_labs_opt_in")
    _firefox_labs_title_locator = (By.ID, "id_firefox_labs_title")
    _firefox_labs_description_locator = (By.ID, "id_firefox_labs_description")
    _requires_restart_locator = (By.ID, "id_requires_restart")

    _displayed_rollout_experience_locator = (
        By.ID,
        "rollout-features-experience",
    )
    _displayed_feature_configs_locator = (By.ID, "rollout-features-config-0")
    _displayed_warn_feature_schema_locator = (
        By.ID,
        "rollout-features-warn-schema",
    )
    _displayed_prevent_pref_conflicts_locator = (
        By.ID,
        "rollout-features-prevent-conflicts",
    )

    def _set_checkbox(self, locator, value):
        checkbox = self._wait_present(locator)
        if checkbox.is_selected() != value:
            self.click_element(locator)

    def _get_displayed_boolean(self, locator):
        return "fa-check" in self._wait_present(locator).get_attribute("class").split()

    @property
    def rollout_experience(self):
        return self.get_input(self._rollout_experience_locator).get_attribute("value")

    @rollout_experience.setter
    def rollout_experience(self, value):
        self.set_input(self._rollout_experience_locator, value)

    @property
    def feature_configs(self):
        return self._wait_present(self._feature_configs_button_locator).text

    def add_feature_config(self, name):
        form = self._wait_present(self._form_locator)
        self.set_bootstrap_select(
            self._feature_configs_button_locator,
            self._feature_configs_search_locator,
            [name],
        )
        self.wait.until(EC.staleness_of(form))
        self._wait_present(self._form_locator)
        return self

    @property
    def warn_feature_schema(self):
        return self._wait_present(self._warn_feature_schema_locator).is_selected()

    @warn_feature_schema.setter
    def warn_feature_schema(self, value):
        self._set_checkbox(self._warn_feature_schema_locator, value)

    @property
    def prevent_pref_conflicts(self):
        return self._wait_present(self._prevent_pref_conflicts_locator).is_selected()

    @prevent_pref_conflicts.setter
    def prevent_pref_conflicts(self, value):
        self._set_checkbox(self._prevent_pref_conflicts_locator, value)

    @property
    def is_firefox_labs_opt_in(self):
        return self._wait_present(self._is_firefox_labs_opt_in_locator).is_selected()

    @is_firefox_labs_opt_in.setter
    def is_firefox_labs_opt_in(self, value):
        checkbox = self._wait_present(self._is_firefox_labs_opt_in_locator)
        if checkbox.is_selected() == value:
            return

        form = self._wait_present(self._form_locator)
        self.click_element(self._is_firefox_labs_opt_in_locator)
        self.wait.until(EC.staleness_of(form))
        self._wait_present(self._form_locator)

    @property
    def firefox_labs_title(self):
        return self.get_input(self._firefox_labs_title_locator).get_attribute("value")

    @firefox_labs_title.setter
    def firefox_labs_title(self, value):
        self.set_input(self._firefox_labs_title_locator, value)

    @property
    def firefox_labs_description(self):
        return self.get_input(self._firefox_labs_description_locator).get_attribute(
            "value"
        )

    @firefox_labs_description.setter
    def firefox_labs_description(self, value):
        self.set_input(self._firefox_labs_description_locator, value)

    @property
    def requires_restart(self):
        return self._wait_present(self._requires_restart_locator).is_selected()

    @requires_restart.setter
    def requires_restart(self, value):
        self._set_checkbox(self._requires_restart_locator, value)

    @property
    def displayed_rollout_experience(self):
        return self._wait_present(self._displayed_rollout_experience_locator).text

    @property
    def displayed_feature_configs(self):
        self._wait_present(self._displayed_rollout_experience_locator)
        return [
            element.text
            for element in self.selenium.find_elements(
                *self._displayed_feature_configs_locator
            )
        ]

    @property
    def displayed_warn_feature_schema(self):
        return self._get_displayed_boolean(self._displayed_warn_feature_schema_locator)

    @property
    def displayed_prevent_pref_conflicts(self):
        return self._get_displayed_boolean(self._displayed_prevent_pref_conflicts_locator)
