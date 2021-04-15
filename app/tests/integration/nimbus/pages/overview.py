from nimbus.pages.base import Base
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class OverviewPage(Base):
    """Experiment Overview Page."""

    _public_description_locator = (By.CSS_SELECTOR, "#publicDescription")
    _risk_mitigation_locator = (By.CSS_SELECTOR, "#riskMitigationLink")
    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditOverview")

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

    @property
    def risk_mitigation(self):
        return self.find_element(*self._risk_mitigation_locator).text

    @risk_mitigation.setter
    def risk_mitigation(self, text=None):
        name = self.find_element(*self._risk_mitigation_locator)
        name.send_keys(f"{text}")
