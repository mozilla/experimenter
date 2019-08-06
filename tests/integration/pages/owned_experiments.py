"""Representaion of the Owned Experiments Page."""

from selenium.webdriver.common.by import By

from pages.base import Base


class OwnedExperiments(Base):

    _owned_text_locator = (By.CSS_SELECTOR, ".m-0")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(
                *self._owned_text_locator
            ).is_displayed()
        )
        return self

    @property
    def count(self):
        """Return the number of owned experiments."""
        num = self.find_element(*self._owned_text_locator).text
        return int(num.split()[0])
