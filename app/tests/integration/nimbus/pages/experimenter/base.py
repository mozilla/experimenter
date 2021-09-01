import time

from nimbus.pages.base import Base
from selenium.webdriver.common.by import By


class ExperimenterBase(Base):
    """Experimenter Base page."""

    _save_btn_locator = (By.CSS_SELECTOR, "#save-button")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-button")

    def save_and_continue(self):
        element = self.selenium.find_element(*self._save_continue_btn_locator)
        element.click()

    def save_btn(self):
        self.find_element(*self._save_btn_locator).click()
        time.sleep(1)

    def next_btn(self):
        pass

    def cancel_btn(self):
        pass
