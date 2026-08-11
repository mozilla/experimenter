from selenium.webdriver.common.by import By

from nimbus.pages.rollouts.form_base import FormBase


class RisksSection(FormBase):
    """Risks section of the rollout detail page."""

    PAGE_TITLE = "Rollout Risks"
    CARD_ID = "risks"

    _risk_ai_locators = (
        (By.ID, "id_risk_ai_0"),
        (By.ID, "id_risk_ai_1"),
    )
    _risk_brand_locators = (
        (By.ID, "id_risk_brand_0"),
        (By.ID, "id_risk_brand_1"),
    )
    _risk_revenue_locators = (
        (By.ID, "id_risk_revenue_0"),
        (By.ID, "id_risk_revenue_1"),
    )
    _risk_partner_related_locators = (
        (By.ID, "id_risk_partner_related_0"),
        (By.ID, "id_risk_partner_related_1"),
    )
    _risk_message_locators = (
        (By.ID, "id_risk_message_0"),
        (By.ID, "id_risk_message_1"),
    )

    _displayed_risk_ai_locator = (By.ID, "rollout-risks-ai")
    _displayed_risk_brand_locator = (By.ID, "rollout-risks-brand")
    _displayed_risk_revenue_locator = (By.ID, "rollout-risks-revenue")
    _displayed_risk_partner_related_locator = (
        By.ID,
        "rollout-risks-partner-related",
    )
    _displayed_risk_message_locator = (By.ID, "rollout-risks-message")

    def _get_risk(self, locators):
        return self._wait_present(locators[0]).is_selected()

    def _set_risk(self, locators, value):
        self.click_element(locators[0 if value else 1])

    def _get_displayed_risk(self, locator):
        return "fa-check" in self._wait_present(locator).get_attribute("class").split()

    @property
    def risk_ai(self):
        return self._get_risk(self._risk_ai_locators)

    @risk_ai.setter
    def risk_ai(self, value):
        self._set_risk(self._risk_ai_locators, value)

    @property
    def risk_brand(self):
        return self._get_risk(self._risk_brand_locators)

    @risk_brand.setter
    def risk_brand(self, value):
        self._set_risk(self._risk_brand_locators, value)

    @property
    def risk_revenue(self):
        return self._get_risk(self._risk_revenue_locators)

    @risk_revenue.setter
    def risk_revenue(self, value):
        self._set_risk(self._risk_revenue_locators, value)

    @property
    def risk_partner_related(self):
        return self._get_risk(self._risk_partner_related_locators)

    @risk_partner_related.setter
    def risk_partner_related(self, value):
        self._set_risk(self._risk_partner_related_locators, value)

    @property
    def risk_message(self):
        return self._get_risk(self._risk_message_locators)

    @risk_message.setter
    def risk_message(self, value):
        self._set_risk(self._risk_message_locators, value)

    @property
    def displayed_risk_ai(self):
        return self._get_displayed_risk(self._displayed_risk_ai_locator)

    @property
    def displayed_risk_brand(self):
        return self._get_displayed_risk(self._displayed_risk_brand_locator)

    @property
    def displayed_risk_revenue(self):
        return self._get_displayed_risk(self._displayed_risk_revenue_locator)

    @property
    def displayed_risk_partner_related(self):
        return self._get_displayed_risk(self._displayed_risk_partner_related_locator)

    @property
    def displayed_risk_message(self):
        return self._get_displayed_risk(self._displayed_risk_message_locator)
