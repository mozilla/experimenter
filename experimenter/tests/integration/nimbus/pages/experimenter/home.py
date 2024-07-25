from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

from nimbus.models.base_dataclass import (
    BaseExperimentApplications,
)
from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.summary import SummaryPage


class HomePage(ExperimenterBase):
    """Nimbus Home page."""

    PAGE_TITLE = "Home Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#PageHome-page")
    _table_experiment_link_locator = (By.CSS_SELECTOR, "#experiment-table tr a")
    _create_new_btn_locator = (By.CSS_SELECTOR, "#create-new-button")
    _public_name_locator = (By.CSS_SELECTOR, "#createForm #id_name")
    _hypothesis_locator = (By.CSS_SELECTOR, "#createForm #id_hypothesis")
    _application_select_locator = (By.CSS_SELECTOR, "#createForm #id_application")
    _save_continue_btn_locator = (By.CSS_SELECTOR, '#createForm button[type="submit"]')

    NEXT_PAGE = SummaryPage

    @property
    def table_experiments(self):
        self.wait.until(
            EC.presence_of_element_located(self._table_experiment_link_locator)
        )
        return self.find_elements(*self._table_experiment_link_locator)

    def find_in_table(self, experiment_name):
        experiment_names = [experiment.text for experiment in self.table_experiments]
        assert experiment_name in experiment_names, (
            f"Home Page: Experiment {experiment_name} not found in "
            f"experiments: {experiment_names}"
        )

    def create_new_button(self):
        el = self.wait_for_and_find_element(*self._create_new_btn_locator)
        el.click()

    @property
    def public_name(self):
        return self.wait_for_and_find_element(*self._public_name_locator).text

    @public_name.setter
    def public_name(self, text=None):
        name = self.wait_for_and_find_element(*self._public_name_locator)
        name.send_keys(f"{text}")

    @property
    def hypothesis(self):
        return self.wait_for_and_find_element(*self._hypothesis_locator).text

    @hypothesis.setter
    def hypothesis(self, text=None):
        name = self.wait_for_and_find_element(*self._hypothesis_locator)
        name.send_keys(f" {text}")

    @property
    def application(self):
        return self.wait_for_and_find_element(*self._application_select_locator).text

    @application.setter
    def application(self, app=BaseExperimentApplications.FIREFOX_DESKTOP.value):
        el = self.wait_for_and_find_element(*self._application_select_locator)
        select = Select(el)
        select.select_by_value(app)
