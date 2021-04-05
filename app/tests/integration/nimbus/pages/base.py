"""Base page."""

from pypom import Page, Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Base(Page):

    _save_btn_locator = (By.CSS_SELECTOR, "#save-btn")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue")

    def __init__(self, selenium, base_url, **kwargs):
        super(Base, self).__init__(selenium, base_url, timeout=30, **kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))

        return self

    def save_and_continue(self):
        element = self.selenium.find_element(*self._save_continue_btn_locator)
        element.click()

    def save_btn(self):
        self.find_element(*self._save_btn_locator).click()
        
    def next_btn(self):
        pass

    def cancel_btn(self):
        pass