from nimbus.models.base_dataclass import BaseExperimentAudienceTargetingOptions
from nimbus.pages.experimenter.base import ExperimenterBase
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select


class AudiencePage(ExperimenterBase):
    """Experiment Audience Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditAudience")
    _channel_select_locator = (By.CSS_SELECTOR, "#channel")
    _min_version_select_locator = (By.CSS_SELECTOR, "#minVersion")
    _targeting_select_locator = (By.CSS_SELECTOR, "#targeting")
    _population_fill_locator = (By.CSS_SELECTOR, "#populationPercent")
    _expected_clients_locator = (By.CSS_SELECTOR, "#totalEnrolledClients")
    _enrollment_period_locator = (By.CSS_SELECTOR, "#proposedEnrollment")
    _duration_locator = (By.CSS_SELECTOR, "#proposedDuration")
    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditAudience")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-button")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))
        return self

    def save_and_continue(self):
        element = self.selenium.find_element(*self._save_continue_btn_locator)
        element.click()
        from nimbus.pages.experimenter.summary import SummaryPage

        return SummaryPage(self.driver, self.base_url).wait_for_page_to_load()

    @property
    def channel(self):
        return self.find_element(*self._channel_select_locator).text

    @channel.setter
    def channel(self, channel="Nightly"):
        el = self.find_element(*self._channel_select_locator)
        select = Select(el)
        select.select_by_visible_text(channel)

    @property
    def min_version(self):
        return self.find_element(*self._min_version_select_locator).text

    @min_version.setter
    def min_version(self, version=80):
        el = self.find_element(*self._min_version_select_locator)
        select = Select(el)
        select.select_by_value(f"FIREFOX_{version}")

    @property
    def targeting(self):
        return self.find_element(*self._targeting_select_locator).text

    @targeting.setter
    def targeting(self, targeting=BaseExperimentAudienceTargetingOptions.NO_TARGETING):
        el = self.find_element(*self._targeting_select_locator)
        select = Select(el)
        select.select_by_value(targeting)

    @property
    def percentage(self):
        return self.find_element(*self._population_fill_locator).text

    @percentage.setter
    def percentage(self, text: float) -> None:
        name = self.find_element(*self._population_fill_locator)
        name.clear()
        name.send_keys(f"{text}")

    @property
    def expected_clients(self):
        el = self.find_element(*self._expected_clients_locator)
        return el.get_attribute("value")

    @expected_clients.setter
    def expected_clients(self, text):
        el = self.find_element(*self._expected_clients_locator)
        el.send_keys(text)
