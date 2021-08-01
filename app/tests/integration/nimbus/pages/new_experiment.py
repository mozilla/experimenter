from nimbus.pages.base import Base
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select


class NewExperiment(Base):
    """New Experiment Page."""

    _public_name_locator = (By.CSS_SELECTOR, "#name")
    _hypothesis_locator = (By.CSS_SELECTOR, "#hypothesis")
    _application_select_locator = (By.CSS_SELECTOR, "#application")
    _cancel_btn_locator = (By.CSS_SELECTOR, ".btn-light")
    _next_btn_locator = (By.CSS_SELECTOR, "#submit-button")
    _page_wait_locator = (By.CSS_SELECTOR, "#PageNew-page")  # page needs a good selector

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))

        return self

    def fill(self, experiment):
        self.public_name = experiment.public_name
        self.hypothesis = experiment.hypothesis
        self.application = experiment.application

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

    def save_and_continue(self):
        el = self.find_element(*self._next_btn_locator)
        el.click()
        from nimbus.pages.overview import OverviewPage

        return OverviewPage(self.driver, self.base_url).wait_for_page_to_load()
