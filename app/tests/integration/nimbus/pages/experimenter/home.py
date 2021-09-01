from pypom import Page, Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class HomePage(Page):
    """Nimbus Home page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageHome-page")
    _create_new_btn_locator = (By.CSS_SELECTOR, "#create-new-button")

    def wait_for_page_to_load(self):
        self.wait.until(EC.visibility_of_element_located(self._page_wait_locator))
        return self

    @property
    def tables(self):
        _table_locator = (By.CSS_SELECTOR, ".active .directory-table")
        self.wait.until(EC.presence_of_element_located(_table_locator))
        tables = self.find_elements(*_table_locator)
        return [self.Tables(self, el) for el in tables]

    @property
    def tabs(self):
        _tabs_locator = (By.CSS_SELECTOR, ".nav-item")
        return self.find_elements(*_tabs_locator)

    @property
    def active_tab_text(self):
        _active_tab_locator = (By.CSS_SELECTOR, ".nav-item.active")
        el = self.find_element(*_active_tab_locator)
        return el.text

    def create_new_button(self):
        el = self.find_element(*self._create_new_btn_locator)
        el.click()
        from nimbus.pages.experimenter.new_experiment import NewExperiment

        return NewExperiment(self.driver, self.base_url).wait_for_page_to_load()

    class Tables(Region):

        _experiment_link_locator = (By.CSS_SELECTOR, "tr a")

        @property
        def experiments(self):
            self.wait.until(EC.presence_of_element_located(self._experiment_link_locator))
            return self.find_elements(*self._experiment_link_locator)
