from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.experimenter.base import Base


class HomePage(Base):
    """Nimbus Home page."""

    PAGE_TITLE = "Home Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#PageHome-page")
    _create_new_btn_locator = (By.CSS_SELECTOR, "#create-new-button")
    _table_experiment_link_locator = (By.CSS_SELECTOR, "#experiment-table tr a")

    def create_new_button(self):
        el = self.wait_for_and_find_element(*self._create_new_btn_locator)
        el.click()
        from nimbus.pages.experimenter.new_experiment import NewExperiment

        return NewExperiment(self.driver, self.base_url).wait_for_page_to_load()

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
