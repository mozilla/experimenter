from pypom import Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.experimenter.base import Base


class HomePage(Base):
    """Nimbus Home page."""

    PAGE_TITLE = "Home Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#PageHome-page")
    _create_new_btn_locator = (By.CSS_SELECTOR, "#create-new-button")

    @property
    def tables(self):
        _table_locator = (By.CSS_SELECTOR, ".active .directory-table")
        self.wait.until(EC.presence_of_element_located(_table_locator))
        tables = self.find_elements(*_table_locator)
        return [self.Tables(self, el) for el in tables]

    @property
    def tabs(self):
        _tabs_locator = (By.CSS_SELECTOR, ".nav-item")
        return self.wait_for_and_find_elements(*_tabs_locator)

    @property
    def active_tab_text(self):
        _active_tab_locator = (By.CSS_SELECTOR, ".nav-item.active")
        el = self.wait_for_and_find_element(*_active_tab_locator)
        return el.text

    def create_new_button(self):
        el = self.wait_for_and_find_element(*self._create_new_btn_locator)
        el.click()
        from nimbus.pages.experimenter.new_experiment import NewExperiment

        return NewExperiment(self.driver, self.base_url).wait_for_page_to_load()

    def find_in_table(self, table_name, experiment_name):
        table_experiments = self.tables[0]
        assert (
            table_name in self.active_tab_text
        ), f"Home Page: Table {table_name} not found in {self.active_tab_text}"
        experiment_names = [
            experiment.text for experiment in table_experiments.experiments
        ]
        assert experiment_name in experiment_names, (
            f"Home Page: Experiment {experiment_name} not found in "
            "{table_name} experiments: {experiment_names}"
        )

    class Tables(Region):

        _experiment_link_locator = (By.CSS_SELECTOR, "tr a")

        @property
        def experiments(self):
            self.wait.until(EC.presence_of_element_located(self._experiment_link_locator))
            return self.find_elements(*self._experiment_link_locator)
