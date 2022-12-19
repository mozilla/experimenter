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
    _pref_locator = (By.CSS_SELECTOR, "tr > th > span")

    def __init__(self, selenium, **kwargs):
        super().__init__(selenium, timeout=80, **kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._search_bar_locator))
        return self

    def wait_for_pref_flip(self, pref, pref_value):
        timeout = time.time() + 60 * 5
        error = None
        while time.time() < timeout:
            try:
                search_bar = self.find_element(*self._search_bar_locator)
                search_bar.send_keys(pref)
                self.wait.until(EC.presence_of_element_located(self._row_locator))
                elements = self.find_elements(*self._row_locator)
                assert pref_value in [
                    element.text for element in elements
                ], "Pref not found"
            except (Exception, AssertionError) as e:
                time.sleep(2)
                error = e
            else:
                return True
        raise (error)

    def flip_pref(self, pref):
        timeout = time.time() + 15
        error = None
        while time.time() < timeout:
            try:
                search_bar = self.find_element(*self._search_bar_locator)
                search_bar.send_keys(pref)
                self.wait.until(EC.presence_of_element_located(self._row_locator))
                actual_row = (By.CSS_SELECTOR, "table > tr")
                new_pref_locator = (By.CSS_SELECTOR, "th > span")
                elements = self.find_elements(*actual_row)
                el = [
                    element
                    for element in elements
                    if pref in element.find_element(*new_pref_locator).text
                ][0]
                el.find_element(By.CSS_SELECTOR, ".cell-edit").click()
            except Exception as e:
                error = e
                time.sleep(2)
                self.selenium.get("about:config")
                self.wait_for_page_to_load()
            else:
                return True
        raise (error)

    def get_pref_value(self, pref):
        self.selenium.get("about:config")
        self = self.wait_for_page_to_load()
        search_bar = self.find_element(*self._search_bar_locator)
        search_bar.send_keys(pref)
        self.wait.until(EC.presence_of_element_located(self._row_locator))
        actual_row = (By.CSS_SELECTOR, "table > tr")
        new_pref_locator = (By.CSS_SELECTOR, "th > span")
        elements = self.find_elements(*actual_row)
        el = [
            element
            for element in elements
            if pref in element.find_element(*new_pref_locator).text
        ][0]
        return el.find_element(By.CSS_SELECTOR, ".cell-value").text
