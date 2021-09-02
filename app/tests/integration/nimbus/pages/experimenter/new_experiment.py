from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.overview import OverviewPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


class NewExperiment(ExperimenterBase):
    """New Experiment Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageNew-page")
    _public_name_locator = (By.CSS_SELECTOR, "#name")
    _hypothesis_locator = (By.CSS_SELECTOR, "#hypothesis")
    _application_select_locator = (By.CSS_SELECTOR, "#application")
    _cancel_btn_locator = (By.CSS_SELECTOR, ".btn-light")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#submit-button")
    NEXT_PAGE = OverviewPage

    @property
    def public_name(self):
        return self.find_element(*self._public_name_locator).text

    @public_name.setter
    def public_name(self, text=None):
        name = self.find_element(*self._public_name_locator)
        name.send_keys(f"{text}")

    @property
    def hypothesis(self):
        return self.find_element(*self._hypothesis_locator).text

    @hypothesis.setter
    def hypothesis(self, text=None):
        name = self.find_element(*self._hypothesis_locator)
        name.send_keys(f" {text}")

    @property
    def application(self):
        return self.find_element(*self._application_select_locator).text

    @application.setter
    def application(self, app="DESKTOP"):
        el = self.find_element(*self._application_select_locator)
        select = Select(el)
        select.select_by_value(app)
