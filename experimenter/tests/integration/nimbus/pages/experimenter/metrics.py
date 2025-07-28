from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from nimbus.pages.experimenter.audience import AudiencePage
from nimbus.pages.experimenter.base import ExperimenterBase


class MetricsPage(ExperimenterBase):
    """Experiment Metrics Page."""

    PAGE_TITLE = "Metrics Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#metrics-form")
    _outcomes_selector_locator = (By.CSS_SELECTOR, ".card-body button")
    _outcomes_input_locator = (By.CSS_SELECTOR, ".card-body input")
    _outcomes_text_locator = (
        By.CSS_SELECTOR,
        ".card-body button .filter-option-inner-inner",
    )
    _secondary_outcome_root_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='secondary-outcomes']",
    )
    _multifeature_element_locator = (By.CSS_SELECTOR, "div[class$='-multiValue']")
    NEXT_PAGE = AudiencePage

    @property
    def primary_outcomes(self):
        els = self.wait_for_and_find_elements(*self._outcomes_text_locator)
        return els[0]

    def set_primary_outcomes(self, values=None):
        els = self.wait_for_and_find_elements(*self._outcomes_selector_locator)
        els[0].click()
        search_box = self.wait_for_and_find_elements(*self._outcomes_input_locator)
        search_box[0].send_keys(values, Keys.RETURN)

    @property
    def secondary_outcomes(self):
        els = self.wait_for_and_find_elements(*self._outcomes_text_locator)
        return els[1]

    def set_secondary_outcomes(self, values=None):
        els = self.wait_for_and_find_elements(*self._outcomes_selector_locator)
        els[1].click()
        search_box = self.wait_for_and_find_elements(*self._outcomes_input_locator)
        search_box[1].send_keys(values, Keys.RETURN)
