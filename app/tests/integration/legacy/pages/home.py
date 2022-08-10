from pages.base import Base
from selenium.webdriver.common.by import By


class Home(Base):

    _create_experiment_btn_locator = (By.CSS_SELECTOR, "a.col.btn-primary")
    _page_wait_locator = (By.CSS_SELECTOR, "body.page-list-view")
    _load_legacy_page = (By.CSS_SELECTOR, "#legacy_page_link")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._load_legacy_page).is_displayed())
        self.find_element(*self._load_legacy_page).click()
        # wait for new tab
        original_window = self.selenium.current_window_handle
        for window_handle in self.selenium.window_handles:
            if window_handle != original_window:
                self.selenium.switch_to.window(window_handle)
                break

        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    def create_experiment(self):
        self.find_element(*self._create_experiment_btn_locator).click()
        from pages.experiment_overview import ExperimentOverview

        return ExperimentOverview(self.driver, self.base_url).wait_for_page_to_load()
