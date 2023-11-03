import threading
import time

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
                sleep_thread = threading.Thread(
                    target=self.non_blocking_sleep, args=(10,)
                )
                sleep_thread.start()
                sleep_thread.join()  # Wait for the thread to finish sleeping
                selenium.refresh()
                return False
            else:
                return True

        self.wait.until(_wait_for_it, message=message)

    def wait_for_locator(self, locator, description=None):
        if not description:
            description = "locator"
        self.wait.until(
            EC.presence_of_all_elements_located(locator),
            message=f"{self.PAGE_TITLE}: could not find {description}",
        )

    def wait_for_and_find_element(self, strategy, locator, description=None):
        self.wait_for_locator((strategy, locator), description)
        return self.find_element(strategy, locator)

    def wait_for_and_find_elements(self, strategy, locator, description=None):
        self.wait_for_locator((strategy, locator), description)
        return self.find_elements(strategy, locator)

    def non_blocking_sleep(self, seconds):
        time.sleep(seconds)
