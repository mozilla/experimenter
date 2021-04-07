from pypom import Page, Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class HomePage(Page):
    """Nimbus Home page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#create-new-button")

    def __init__(self, selenium, base_url, **kwargs):
        super(HomePage, self).__init__(selenium, base_url, timeout=30, **kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))

        return self

    def create_new_button(self):
        el = self.find_element(*self._page_wait_locator)
        el.click()
        from nimbus.pages.new_experiment import NewExperiment

        return NewExperiment(self.driver, self.base_url).wait_for_page_to_load()