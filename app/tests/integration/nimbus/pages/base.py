from pypom import Page
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


class Base(Page):
    """Base page."""

    def __init__(self, selenium, base_url, **kwargs):
        super().__init__(selenium, base_url, timeout=80, **kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))
        return self

    def wait_with_refresh(self, locator, message):
        def _wait_for_it(selenium):
            try:
                self.wait_for_page_to_load()
                selenium.find_element(*locator)
            except NoSuchElementException:
                selenium.refresh()
                return False
            else:
                return True

        self.wait.until(_wait_for_it, message=message)
