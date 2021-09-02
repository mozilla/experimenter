from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.branches import BranchesPage
from selenium.webdriver.common.by import By


class OverviewPage(ExperimenterBase):
    """Experiment Overview Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditOverview")
    _public_description_locator = (By.CSS_SELECTOR, "#publicDescription")
    _risk_brand_locator = (By.CSS_SELECTOR, "#riskBrand-false")
    _risk_revenue_locator = (By.CSS_SELECTOR, "#riskRevenue-false")
    _risk_partner_locator = (By.CSS_SELECTOR, "#riskPartnerRelated-false")
    NEXT_PAGE = BranchesPage

    @property
    def public_description(self):
        return self.find_element(*self._public_description_locator).text

    @public_description.setter
    def public_description(self, text=None):
        name = self.find_element(*self._public_description_locator)
        name.send_keys(f"{text}")

    def select_risk_brand_false(self):
        el = self.find_element(*self._risk_brand_locator)
        el.click()

    def select_risk_revenue_false(self):
        el = self.find_element(*self._risk_revenue_locator)
        el.click()

    def select_risk_partner_false(self):
        el = self.find_element(*self._risk_partner_locator)
        el.click()
