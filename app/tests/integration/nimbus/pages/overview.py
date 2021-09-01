from nimbus.pages.base import Base
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class OverviewPage(Base):
    """Experiment Overview Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditOverview")
    _public_description_locator = (By.CSS_SELECTOR, "#publicDescription")
    _risk_brand_locator = (By.CSS_SELECTOR, "#riskBrand-false")
    _risk_revenue_locator = (By.CSS_SELECTOR, "#riskRevenue-false")
    _risk_partner_locator = (By.CSS_SELECTOR, "#riskPartnerRelated-false")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))

        return self

    def save_and_continue(self):
        element = self.selenium.find_element(*self._save_continue_btn_locator)
        element.click()
        from nimbus.pages.branches import BranchesPage

        return BranchesPage(self.driver, self.base_url).wait_for_page_to_load()

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
