from selenium.webdriver.common.by import By

from nimbus.pages.experimenter.audience import AudiencePage
from nimbus.pages.experimenter.base import ExperimenterBase


class MetricsPage(ExperimenterBase):
    """Experiment Metrics Page."""

    PAGE_TITLE = "Metrics Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#metrics-form")
    _primary_outcomes_button_locator = (By.CSS_SELECTOR, ".card-body button")
    _primary_outcomes_input_locator = (By.CSS_SELECTOR, ".card-body input")
    _outcomes_text_locator = (
        By.CSS_SELECTOR,
        ".card-body button .filter-option-inner-inner",
    )
    NEXT_PAGE = AudiencePage

    @property
    def primary_outcomes(self):
        els = self.wait_for_and_find_elements(*self._outcomes_text_locator)
        return els[0]

    def set_primary_outcomes(self, values=None):
        # Primary outcomes is the first Bootstrap Select on the page
        els = self.wait_for_and_find_elements(*self._primary_outcomes_button_locator)
        els[0].click()
        search_boxes = self.wait_for_and_find_elements(
            *self._primary_outcomes_input_locator
        )
        search_boxes[0].send_keys(values)
        from selenium.webdriver.common.keys import Keys

        search_boxes[0].send_keys(Keys.RETURN)

    @property
    def secondary_outcomes(self):
        els = self.wait_for_and_find_elements(*self._outcomes_text_locator)
        return els[1]

    def set_secondary_outcomes(self, values=None):
        # Secondary outcomes is the second Bootstrap Select on the page
        els = self.wait_for_and_find_elements(*self._primary_outcomes_button_locator)
        els[1].click()
        search_boxes = self.wait_for_and_find_elements(
            *self._primary_outcomes_input_locator
        )
        search_boxes[1].send_keys(values)
        from selenium.webdriver.common.keys import Keys

        search_boxes[1].send_keys(Keys.RETURN)
