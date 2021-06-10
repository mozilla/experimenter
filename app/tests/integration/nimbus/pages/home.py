from pypom import Page, Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class HomePage(Page):
    """Nimbus Home page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#create-new-button")

    def __init__(self, selenium, base_url, **kwargs):
        super(HomePage, self).__init__(selenium, base_url, timeout=30, **kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))

        return self

    @property
    def tables(self):
        _table_locator = (By.CSS_SELECTOR, ".tab-content table")
        self.wait.until(EC.presence_of_element_located(_table_locator))
        tables = self.find_elements(*_table_locator)
        return [self.Tables(self, el) for el in tables]

    def create_new_button(self):
        el = self.find_element(*self._page_wait_locator)
        el.click()
        from nimbus.pages.new_experiment import NewExperiment

        return NewExperiment(self.driver, self.base_url).wait_for_page_to_load()

    class Tables(Region):

        _table_name_locator = (By.CSS_SELECTOR, ".font-weight-bold")
        _experiment_link_locator = (By.CSS_SELECTOR, "tr a")

        @property
        def table_name(self):
            el = self.find_element(*self._table_name_locator)
            return el.text

        @property
        def experiments(self):
            self.wait.until(EC.presence_of_element_located(self._experiment_link_locator))
            return self.find_elements(*self._experiment_link_locator)
