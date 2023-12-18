from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.summary import SummaryPage


class AudiencePage(ExperimenterBase):
    """Experiment Audience Page."""

    PAGE_TITLE = "Audience Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditAudience")
    _channel_select_locator = (By.CSS_SELECTOR, "#channel")
    _min_version_select_locator = (By.CSS_SELECTOR, "#minVersion")
    _targeting_select_locator = (By.CSS_SELECTOR, "#targeting")
    _population_fill_locator = (
        By.CSS_SELECTOR,
        '[data-testid="population-percent-text"]',
    )
    _expected_clients_locator = (By.CSS_SELECTOR, "#totalEnrolledClients")
    _enrollment_period_locator = (By.CSS_SELECTOR, "#proposedEnrollment")
    _duration_locator = (By.CSS_SELECTOR, "#proposedDuration")
    _locales_input_locator = (By.CSS_SELECTOR, "div[data-testid='locales'] input")
    _locales_value_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='locales'] > div:nth-child(1)",
    )
    _countries_input_locator = (By.CSS_SELECTOR, "div[data-testid='countries'] input")
    _countries_value_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='countries'] > div:nth-child(1)",
    )
    _languages_input_locator = (By.CSS_SELECTOR, "div[data-testid='languages'] input")
    _languages_value_locator = (
        By.CSS_SELECTOR,
        "div[data-testid='languages'] > div:nth-child(1)",
    )
    _first_run_checkbox_locator = (By.CSS_SELECTOR, '[data-testid="isFirstRun"]')
    _release_date_locator = (By.CSS_SELECTOR, '[data-testid="proposedReleaseDate"]')
    _saved_locator = (By.CSS_SELECTOR, "form.was-validated")

    NEXT_PAGE = SummaryPage

    def save_and_continue(self):
        # Explicitly save and wait for save to complete before continuing
        # to prevent intermittent failures where summary loads before saving
        # audience is complete
        self.save()
        self.wait_for_locator(self._saved_locator)

        return super().save_and_continue()

    @property
    def channel(self):
        return self.wait_for_and_find_element(*self._channel_select_locator).text

    @channel.setter
    def channel(self, channel="Nightly"):
        el = self.wait_for_and_find_element(*self._channel_select_locator)
        select = Select(el)
        select.select_by_visible_text(channel)

    @property
    def min_version(self):
        return self.wait_for_and_find_element(*self._min_version_select_locator).text

    @min_version.setter
    def min_version(self, version=80):
        el = self.wait_for_and_find_element(*self._min_version_select_locator)
        select = Select(el)
        select.select_by_value(f"FIREFOX_{version}")

    @property
    def targeting(self):
        return self.wait_for_and_find_element(*self._targeting_select_locator).text

    @targeting.setter
    def targeting(self, targeting=""):
        el = self.wait_for_and_find_element(*self._targeting_select_locator)
        select = Select(el)
        select.select_by_value(targeting)

    @property
    def percentage(self):
        return self.wait_for_and_find_element(*self._population_fill_locator).text

    @percentage.setter
    def percentage(self, text) -> None:
        name = self.wait_for_and_find_element(*self._population_fill_locator)
        name.clear()
        name.send_keys(f"{text}")

    @property
    def expected_clients(self):
        el = self.wait_for_and_find_element(*self._expected_clients_locator)
        return el.get_attribute("value")

    @expected_clients.setter
    def expected_clients(self, text):
        el = self.wait_for_and_find_element(*self._expected_clients_locator)
        el.send_keys(text)

    @property
    def locales(self):
        return [
            element.text
            for element in self.wait_for_and_find_elements(*self._locales_value_locator)
        ]

    @locales.setter
    def locales(self, text=None):
        el = self.wait_for_and_find_element(*self._locales_input_locator)
        for _ in text:
            el.send_keys(f"{_}")
            el.send_keys(Keys.ENTER)

    @property
    def countries(self):
        return [
            element.text
            for element in self.wait_for_and_find_elements(*self._countries_value_locator)
        ]

    @countries.setter
    def countries(self, text=None):
        el = self.wait_for_and_find_element(*self._countries_input_locator)
        for _ in text:
            el.send_keys(f"{_}")
            el.send_keys(Keys.ENTER)

    @property
    def languages(self):
        return [
            element.text
            for element in self.wait_for_and_find_elements(*self._languages_value_locator)
        ]

    @languages.setter
    def languages(self, text=None):
        el = self.wait_for_and_find_element(*self._languages_input_locator)
        for char in text:
            el.send_keys(char)
            el.send_keys(Keys.ENTER)

    @property
    def is_first_run(self):
        return self.wait_for_and_find_element(
            *self._first_run_checkbox_locator, "is first run"
        )

    def make_first_run(self):
        self.wait_for_and_find_element(
            *self._first_run_checkbox_locator, "is_first_run"
        ).click()

    @property
    def proposed_release_date(self):
        el = self.wait_for_and_find_element(*self._release_date_locator)
        return el.get_attribute("value")

    @proposed_release_date.setter
    def proposed_release_date(self, text=None):
        el = self.wait_for_and_find_element(*self._release_date_locator)
        el.send_keys(text)

    def wait_until_release_date_not_found(self):
        self.wait.until_not(
            EC.presence_of_element_located(self._release_date_locator),
            message="Audience Page: could not find release date",
        )

    def wait_until_first_run_not_found(self):
        self.wait.until_not(
            EC.presence_of_element_located(self._first_run_checkbox_locator),
            message="Audience Page: could not find first run checkbox",
        )
