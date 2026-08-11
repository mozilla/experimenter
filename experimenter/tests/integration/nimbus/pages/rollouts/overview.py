from selenium.webdriver.common.by import By

from nimbus.pages.rollouts.form_base import FormBase


class OverviewSection(FormBase):
    """Overview section of the rollout detail page."""

    PAGE_TITLE = "Rollout Overview"
    CARD_ID = "overview"

    _name_locator = (By.ID, "id_name")
    _hypothesis_locator = (By.ID, "id_hypothesis")
    _public_description_locator = (By.ID, "id_public_description")
    _application_locator = (By.ID, "id_application")
    _displayed_name_locator = (By.ID, "rollout-overview-name")
    _displayed_hypothesis_locator = (By.ID, "rollout-overview-hypothesis")
    _displayed_public_description_locator = (
        By.ID,
        "rollout-overview-public-description",
    )

    @property
    def name(self):
        return self.get_input(self._name_locator).get_attribute("value")

    @name.setter
    def name(self, value):
        self.set_input(self._name_locator, value)

    @property
    def hypothesis(self):
        return self.get_input(self._hypothesis_locator).get_attribute("value")

    @hypothesis.setter
    def hypothesis(self, value):
        self.set_input(self._hypothesis_locator, value)

    @property
    def public_description(self):
        return self.get_input(self._public_description_locator).get_attribute("value")

    @public_description.setter
    def public_description(self, value):
        self.set_input(self._public_description_locator, value)

    @property
    def application(self):
        return self.get_select(self._application_locator).get_attribute("value")

    @property
    def displayed_name(self):
        return self._wait_present(self._displayed_name_locator).text

    @property
    def displayed_hypothesis(self):
        return self._wait_present(self._displayed_hypothesis_locator).text

    @property
    def displayed_public_description(self):
        return self._wait_present(self._displayed_public_description_locator).text
