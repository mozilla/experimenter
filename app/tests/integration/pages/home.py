from selenium.webdriver.common.by import By

from pages.base import Base


class Home(Base):

    _create_experiment_btn_locator = (By.CSS_SELECTOR, "a.col.btn-primary")
    _page_wait_locator = (By.CSS_SELECTOR, "body.page-list-view")

    def create_experiment(self):
        self.find_element(*self._create_experiment_btn_locator).click()
        from pages.experiment_overview import ExperimentOverview

        return ExperimentOverview(self.driver, self.base_url).wait_for_page_to_load()
