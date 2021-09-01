from nimbus.pages.experimenter.base import ExperimenterBase
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class MetricsPage(ExperimenterBase):
    """Experiment Metrics Page.."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditMetrics")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-button")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))

        return self

    def save_and_continue(self):
        element = self.selenium.find_element(*self._save_continue_btn_locator)
        element.click()
        from nimbus.pages.experimenter.audience import AudiencePage

        return AudiencePage(self.driver, self.base_url).wait_for_page_to_load()
