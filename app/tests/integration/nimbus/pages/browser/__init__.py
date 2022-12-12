"""Browser Model"""
import time

from pypom import Page
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Browser:
    def execute_script(selenium, *args, script=None, context=None):
        if "chrome" in context:
            with selenium.context(selenium.CONTEXT_CHROME):
                return selenium.execute_script(script, *args)
        else:
            return selenium.execute_script


class AboutConfig(Page):

    URL_TEMPLATE = "about:config"

    _search_bar_locator = (By.ID, "about-config-search")
    _row_locator = (By.CSS_SELECTOR, "tr > td > span > span")

    def __init__(self, selenium, **kwargs):
        super().__init__(selenium, timeout=80, **kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._search_bar_locator))
        return self

    def wait_for_pref_flip(self, pref=None, pref_value=None):
        timeout = time.time() + 60 * 5
        while time.time() < timeout:
            try:
                search_bar = self.find_element(*self._search_bar_locator)
                search_bar.send_keys(pref)
                self.wait.until(EC.presence_of_element_located(self._row_locator))
                elements = self.find_elements(*self._row_locator)
                assert pref in [element.text for element in elements]
            except Exception:
                time.sleep(2)
                return False
            else:
                return True
