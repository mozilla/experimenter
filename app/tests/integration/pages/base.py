"""Base page."""

from pypom import Page, Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Base(Page):

    _save_btn_locator = (By.CSS_SELECTOR, "#save-btn")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-btn")

    def __init__(self, selenium, base_url, **kwargs):
        super(Base, self).__init__(selenium, base_url, timeout=30, **kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))

        return self

    @property
    def header(self):
        """Return the header class."""
        return Header(self)

    def save_and_continue(self):
        element = self.selenium.find_element(*self._save_continue_btn_locator)
        element.click()

    def save_btn(self):
        self.find_element(*self._save_btn_locator).click()
        from pages.experiment_detail import DetailPage

        return DetailPage(self.driver, self.base_url).wait_for_page_to_load()


class Header(Region):

    _current_user_locator = (By.CSS_SELECTOR, ".fa-user")
    _owned_experiments_link_locator = (
        By.CSS_SELECTOR,
        ".container .nocolorstyle:nth-child(1)",
    )
    _subscribed_experiments_link_locator = (
        By.CSS_SELECTOR,
        ".container .nocolorstyle:nth-child(2)",
    )

    @property
    def current_user(self):
        return self.find_element(*self._current_user_locator).text

    def click_owned_experiments(self):
        """Clicks owned experiments link."""
        self.find_element(*self._owned_experiments_link_locator).click()
        from pages.owned_experiments import OwnedExperiments

        return OwnedExperiments(self.driver, self.page.base_url).wait_for_page_to_load()

    def click_subscribed_experiments(self):
        """Clicks subscribed experiments link."""
        self.find_element(*self._subscribed_experiments_link_locator).click()
        from pages.subscribed_experiments import SubscribedExperiments

        return SubscribedExperiments(
            self.driver, self.page.base_url
        ).wait_for_page_to_load()
