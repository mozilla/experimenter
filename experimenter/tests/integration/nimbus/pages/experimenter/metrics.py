from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.experimenter.audience import AudiencePage
from nimbus.pages.experimenter.base import ExperimenterBase


class MetricsPage(ExperimenterBase):
    """Experiment Metrics Page."""

    PAGE_TITLE = "Metrics Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditMetrics")
    _outcomes_selector_locator = (By.CSS_SELECTOR, "#PageEditMetrics .form-group input")
    _primary_outcome_root_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='primary-outcomes']",
    )
    _secondary_outcome_root_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='secondary-outcomes']",
    )
    _multifeature_element_locator = (By.CSS_SELECTOR, "div[class$='-multiValue']")
    NEXT_PAGE = AudiencePage

    @property
    def primary_outcomes(self):
        root_locator = self.wait_for_and_find_element(*self._primary_outcome_root_locator)
        multifeature_el = self.wait_for_and_find_element(*self._multifeature_element_locator)
        # self.wait.until(
        #     EC.presence_of_all_elements_located(
        #         self._multifeature_element_locator
        #     )
        # )
        # multifeature_el = root_locator.find_element(self._multifeature_element_locator)
        return multifeature_el.find_element(By.CSS_SELECTOR, "div")

    def set_primary_outcomes(self, values=None):
        els = self.wait_for_and_find_elements(*self._outcomes_selector_locator)
        els[0].send_keys(values)
        els[0].send_keys(Keys.RETURN)

    @property
    def secondary_outcomes(self):
        # root_locator = self.wait_for_and_find_element(
        #     *self._secondary_outcome_root_locator
        # )
        multifeature_el = self.wait_for_and_find_element(*self._multifeature_element_locator)
        # multifeature_el = root_locator.wait_for_and_find_element(
        #     *self._multifeature_element_locator
        # )
        return multifeature_el.find_element(By.CSS_SELECTOR, "div")

    def set_secondary_outcomes(self, values=None):
        els = self.wait_for_and_find_elements(*self._outcomes_selector_locator)
        els[1].send_keys(values)
        els[1].send_keys(Keys.RETURN)
