import logging
import threading
import time

from pypom import Page
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


class Base(Page):
    """Base page."""

    def __init__(self, selenium, base_url, **kwargs):
        super().__init__(selenium, base_url, timeout=120, **kwargs)
        self.logging = logging

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
                sleep_thread = threading.Thread(
                    target=self.non_blocking_sleep, args=(10,)
                )
                sleep_thread.start()
                sleep_thread.join()  # Wait for the thread to finish sleeping
                return False
            else:
                return True

        self.wait.until(_wait_for_it, message=message)

    def wait_with_refresh_and_assert(self, locator, expected_text , message):
        def _wait_for_it(selenium):
            try:
                self.wait_for_page_to_load()
                el = selenium.find_element(*locator)
                assert el.text == expected_text
            except (NoSuchElementException, AssertionError):
                selenium.refresh()
                sleep_thread = threading.Thread(
                    target=self.non_blocking_sleep, args=(10,)
                )
                sleep_thread.start()
                sleep_thread.join()  # Wait for the thread to finish sleeping
                return False
            else:
                return True

        self.wait.until(_wait_for_it, message=message)

    def wait_for_locator(self, locator, description=None, refresh=False):
        message = f"{self.PAGE_TITLE}: could not find {description}"

        if not description:
            description = "locator"
        if refresh:
            self.wait_with_refresh(locator, message=message)
        else:
            self.wait.until(
                EC.presence_of_all_elements_located(locator),
                message=message,
            )

    def wait_for_and_find_element(
        self, strategy, locator, description=None, refresh=False
    ):
        self.wait_for_locator((strategy, locator), description, refresh=refresh)
        return self.find_element(strategy, locator)

    def wait_for_and_find_elements(self, strategy, locator, description=None):
        self.wait_for_locator((strategy, locator), description)
        return self.find_elements(strategy, locator)

    def non_blocking_sleep(self, seconds):
        time.sleep(seconds)

    def execute_script(self, script, *args):
        self.selenium.execute_script(script, *args)
        time.sleep(2)

    def js_click(self, elem):
        self.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        self.execute_script("arguments[0].click();", elem)
