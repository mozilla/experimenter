import contextlib
import logging
import time

from pypom import Page
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

logger = logging.getLogger(__name__)

HTMX_TRACKER_SCRIPT = """
if (typeof window.__htmxPending === 'undefined') {
    window.__htmxPending = 0;
    document.body.addEventListener('htmx:beforeRequest', function() {
        window.__htmxPending++;
    });
    document.body.addEventListener('htmx:afterSettle', function() {
        window.__htmxPending--;
    });
}
"""


class Base(Page):
    """Base page."""

    def __init__(self, selenium, base_url, **kwargs):
        super().__init__(selenium, base_url, timeout=120, **kwargs)

    # --- Low-level helpers ---

    def _inject_htmx_tracker(self):
        with contextlib.suppress(Exception):
            self.selenium.execute_script(HTMX_TRACKER_SCRIPT)

    def wait_for_htmx(self):
        self.wait.until(
            lambda driver: driver.execute_script(
                "return typeof window.__htmxPending === 'undefined'"
                " || window.__htmxPending === 0"
            ),
            message="Timed out waiting for HTMX requests to settle",
        )

    def _scroll_into_view(self, element):
        self.selenium.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )

    def _wait_clickable(self, locator):
        logger.info(f"_wait_clickable: {locator}")
        self.wait_for_htmx()
        logger.info("_wait_clickable: htmx settled, waiting for clickable")
        self.wait.until(
            EC.element_to_be_clickable(locator),
            message=f"{self.PAGE_TITLE}: {locator} not clickable",
        )
        element = self.find_element(*locator)
        self._scroll_into_view(element)
        logger.info("_wait_clickable: done")
        return self.find_element(*locator)

    def _wait_present(self, locator):
        logger.info(f"_wait_present: {locator}")
        self.wait_for_htmx()
        logger.info("_wait_present: htmx settled, waiting for presence")
        self.wait.until(
            EC.presence_of_element_located(locator),
            message=f"{self.PAGE_TITLE}: {locator} not found",
        )
        logger.info("_wait_present: done")
        return self.find_element(*locator)

    # --- Page lifecycle ---

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))
        self._inject_htmx_tracker()
        return self

    def wait_with_refresh(self, locator, message):
        def _wait_for_it(selenium):
            try:
                self.wait_for_page_to_load()
                selenium.find_element(*locator)
            except NoSuchElementException:
                selenium.refresh()
                time.sleep(5)
                return False
            else:
                return True

        self.wait.until(_wait_for_it, message=message)

    def wait_with_refresh_and_assert(self, locator, expected_text, message):
        def _wait_for_it(selenium):
            try:
                self.wait_for_page_to_load()
                el = selenium.find_element(*locator)
                assert el.text == expected_text
            except (NoSuchElementException, AssertionError):
                selenium.refresh()
                time.sleep(5)
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
            self.wait_for_htmx()
            self.wait.until(
                EC.presence_of_element_located(locator),
                message=message,
            )

    # --- Typed field actions ---
    # Use these in page object setters. Each encapsulates the full
    # wait + interact pattern for its field type.

    def get_input(self, locator):
        logger.info(f"get_input: {locator}")
        return self._wait_clickable(locator)

    def set_input(self, locator, text):
        logger.info(f"set_input: {locator} = '{text}'")
        el = self._wait_clickable(locator)
        el.clear()
        el.send_keys(text)
        logger.info("set_input: done")

    def get_select(self, locator):
        logger.info(f"get_select: {locator}")
        return self._wait_present(locator)

    def set_select(self, locator, value):
        logger.info(f"set_select: {locator} = '{value}'")
        el = self._wait_present(locator)
        Select(el).select_by_value(value)
        logger.info("set_select: done")

    def set_select_by_text(self, locator, text):
        logger.info(f"set_select_by_text: {locator} = '{text}'")
        el = self._wait_present(locator)
        Select(el).select_by_visible_text(text)
        logger.info("set_select_by_text: done")

    def click_element(self, locator):
        logger.info(f"click_element: {locator}")
        el = self._wait_clickable(locator)
        el.click()
        logger.info("click_element: done")

    def js_click(self, elem):
        logger.info("js_click")
        self.wait_for_htmx()
        self.selenium.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});arguments[0].click();",
            elem,
        )
        logger.info("js_click: done")

    def set_autocomplete(self, locator, text):
        logger.info(f"set_autocomplete: {locator} = '{text}'")
        el = self._wait_present(locator)
        self._scroll_into_view(el)
        # Tom Select hides the native input — use JS to focus, set value, and
        # dispatch input + keydown(Enter) events to trigger the widget
        self.selenium.execute_script(
            "var el = arguments[0];"
            "el.focus();"
            "el.value = arguments[1];"
            "el.dispatchEvent(new Event('input', {bubbles: true}));"
            "el.dispatchEvent(new KeyboardEvent('keydown', "
            "  {key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true}));",
            el,
            text,
        )
        logger.info("set_autocomplete: done")

    def set_bootstrap_select(self, button_locator, search_locator, values):
        logger.info(f"set_bootstrap_select: {button_locator} values={values}")
        self.wait_for_htmx()
        self.wait.until(EC.presence_of_all_elements_located(button_locator))
        btn = self.find_element(*button_locator)
        for value in values:
            logger.info(f"set_bootstrap_select: clicking for '{value}'")
            btn.click()
            self.wait.until(EC.presence_of_all_elements_located(search_locator))
            search = self.find_element(*search_locator)
            search.send_keys(value, Keys.RETURN)
        # Dismiss the dropdown by sending Escape to the active element
        ActionChains(self.selenium).send_keys(Keys.ESCAPE).perform()
        logger.info("set_bootstrap_select: done")

    # --- Legacy helpers (used by existing page objects not yet migrated) ---

    def wait_for_and_find_element(
        self, strategy, locator, description=None, refresh=False
    ):
        if refresh:
            self.wait_for_locator((strategy, locator), description, refresh=True)
        else:
            self.wait_for_htmx()
            self.wait.until(
                EC.presence_of_element_located((strategy, locator)),
                message=f"{self.PAGE_TITLE}: could not find {description}",
            )
        element = self.find_element(strategy, locator)
        self._scroll_into_view(element)
        return self.find_element(strategy, locator)

    def wait_for_and_find_elements(self, strategy, locator, description=None):
        self.wait_for_htmx()
        self.wait.until(
            EC.presence_of_all_elements_located((strategy, locator)),
            message=f"{self.PAGE_TITLE}: could not find {description}",
        )
        return self.find_elements(strategy, locator)

    def non_blocking_sleep(self, seconds):
        time.sleep(seconds)

    def execute_script(self, script, *args):
        self.selenium.execute_script(script, *args)
