from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from nimbus.pages.experimenter.audience import AudiencePage
from nimbus.pages.experimenter.base import ExperimenterBase


class MetricsPage(ExperimenterBase):
    """Experiment Metrics Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditMetrics")
    _primary_outcomes_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='primary-outcomes'] div[class$='-multiValue'] div"
    )
    _secondary_outcomes_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='secondary-outcomes'] div[class$='-multiValue'] div"
    )
    _outcome_input_locator = (By.CSS_SELECTOR, "#PageEditMetrics .form-group input")
    NEXT_PAGE = AudiencePage

    @property
    def primary_outcomes(self):
        return [el.text for el in self.find_elements(*self._primary_outcomes_locator)]

    def set_primary_outcomes(self, values=None):
        el = self.find_element(*self._outcome_input_locator)
        el.send_keys(values)
        el.send_keys(Keys.RETURN)

    @property
    def secondary_outcomes(self):
        return [el.text for el in self.find_elements(*self._secondary_outcomes_locator)]

    def set_secondary_outcomes(self, values=None):
        el = self.find_element(*self._outcome_input_locator)
        el.send_keys(values)
        el.send_keys(Keys.RETURN)
