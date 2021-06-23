from nimbus.pages.base import Base
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class SummaryPage(Base):

    _experiment_status_icon_locator = (
        By.CSS_SELECTOR,
        ".header-experiment-status .border-primary",
    )
    _page_wait_locator = (By.CSS_SELECTOR, "#PageSummary")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))
        return self

    @property
    def experiment_status(self):
        el = self.find_element(*self._experiment_status_icon_locator)
        return el.text
