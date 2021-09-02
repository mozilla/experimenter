from nimbus.pages.base import Base
from selenium.webdriver.common.by import By


class ExperimenterBase(Base):
    """Experimenter Base page."""

    _save_btn_locator = (By.CSS_SELECTOR, "#save-button")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-button")
    NEXT_PAGE = None

    def save_and_continue(self):
        element = self.selenium.find_element(*self._save_continue_btn_locator)
        element.click()
        return self.NEXT_PAGE(self.driver, self.base_url).wait_for_page_to_load()
