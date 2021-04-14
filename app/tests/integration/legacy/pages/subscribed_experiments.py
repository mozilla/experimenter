"""Representaion of the Subscribed Experiments Page."""

from pages.base import Base
from selenium.webdriver.common.by import By


class SubscribedExperiments(Base):

    _subscribed_text_locator = (By.CSS_SELECTOR, ".m-0")
    _page_wait_locator = (By.CSS_SELECTOR, "body.page-list-view")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    @property
    def count(self):
        """Return the number of subscribed experiments."""
        num = self.find_element(*self._subscribed_text_locator).text
        return int(num.split()[0])

    @property
    def title(self):
        return self.find_element(*self._subscribed_text_locator).text
