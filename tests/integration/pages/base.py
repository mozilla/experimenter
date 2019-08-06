"""Base page."""

from pypom import Page, Region
from selenium.webdriver.common.by import By


class Base(Page):
    def __init__(self, selenium, base_url, locale="en-US", **kwargs):
        super(Base, self).__init__(
            selenium, base_url, locale=locale, timeout=30, **kwargs
        )

    @property
    def header(self):
        """Return the header class."""
        return Header(self)


class Header(Region):

    _owned_experiments_link_locator = (
        By.CSS_SELECTOR,
        ".container .nocolorstyle:nth-child(1)",
    )

    def click_owned_experiments(self):
        """Clicks owned experiments link."""
        self.find_element(*self._owned_experiments_link_locator).click()
        from pages.owned_experiments import OwnedExperiments

        return OwnedExperiments(
            self.driver, self.page.base_url
        ).wait_for_page_to_load()

    def click_subscribed_experiments(self):
        """Clicks subscribed experiments link."""
        self.find_element(*self._owned_experiments_link_locator).click()
        from pages.subscribed_experiments import SubscribedExperiments

        return SubscribedExperiments(
            self.driver, self.page.base_url
        ).wait_for_page_to_load()
