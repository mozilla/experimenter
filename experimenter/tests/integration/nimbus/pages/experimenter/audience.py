from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.summary import SummaryPage


class AudiencePage(ExperimenterBase):
    """Nimbus Audience page."""

    PAGE_TITLE = "Audience Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#audience-form")
    _channel_select_locator = (By.CSS_SELECTOR, "#id_channel")
    _channels_button_locator = (By.CSS_SELECTOR, '[data-id="id_channels"]')
    _channels_input_locator = (By.CSS_SELECTOR, ".bs-searchbox input")
    _channels_text_locator = (By.CSS_SELECTOR, "#id_channels .filter-option-inner-inner")
    _min_version_select_locator = (By.CSS_SELECTOR, "#id_firefox_min_version")
    _targeting_select_locator = (By.CSS_SELECTOR, "#id_targeting_config_slug")
    _population_fill_locator = (By.CSS_SELECTOR, "#id_population_percent")
    _expected_clients_locator = (By.CSS_SELECTOR, "#id_total_enrolled_clients")
    _saved_locator = (By.CSS_SELECTOR, "#sidebar .text-success")
    _locales_button_locator = (
        By.CSS_SELECTOR,
        'div[data-testid="locales"] [data-id="id_locales"]',
    )
    _locales_input_locator = (
        By.CSS_SELECTOR,
        'div[data-testid="locales"] .bs-searchbox input',
    )
    _countries_button_locator = (
        By.CSS_SELECTOR,
        'div[data-testid="countries"] [data-id="id_countries"]',
    )
    _countries_input_locator = (
        By.CSS_SELECTOR,
        'div[data-testid="countries"] .bs-searchbox input',
    )
    _languages_button_locator = (
        By.CSS_SELECTOR,
        'div[data-testid="languages"] [data-id="id_languages"]',
    )
    _languages_input_locator = (
        By.CSS_SELECTOR,
        'div[data-testid="languages"] .bs-searchbox input',
    )
    _first_run_locator = (By.CSS_SELECTOR, "#id_is_first_run")
    _release_date_locator = (By.CSS_SELECTOR, "#id_proposed_release_date")

    NEXT_PAGE = SummaryPage

    @property
    def channel(self):
        return self.get_select(self._channel_select_locator).text

    @channel.setter
    def channel(self, channel="Nightly"):
        self.set_select_by_text(self._channel_select_locator, channel)

    @property
    def channels(self):
        return self.wait_for_and_find_elements(*self._channels_text_locator)[0]

    @channels.setter
    def channels(self, channels):
        self.set_bootstrap_select(
            self._channels_button_locator, self._channels_input_locator, channels
        )

    @property
    def min_version(self):
        return self.get_select(self._min_version_select_locator).text

    @min_version.setter
    def min_version(self, version=80):
        self.set_select(self._min_version_select_locator, f"{version}")

    @property
    def targeting(self):
        return self.get_select(self._targeting_select_locator).text

    @targeting.setter
    def targeting(self, targeting=""):
        self.set_select(self._targeting_select_locator, targeting)

    @property
    def percentage(self):
        return self.get_input(self._population_fill_locator).text

    @percentage.setter
    def percentage(self, text):
        el = self.get_input(self._population_fill_locator)
        el.click()
        self.execute_script("arguments[0].setAttribute('value', arguments[1]);", el, text)

    @property
    def expected_clients(self):
        return self.get_input(self._expected_clients_locator).text

    @expected_clients.setter
    def expected_clients(self, text):
        self.set_input(self._expected_clients_locator, text)

    @property
    def proposed_release_date(self):
        return self.get_input(self._release_date_locator).get_attribute("value")

    @proposed_release_date.setter
    def proposed_release_date(self, text):
        self.set_input(self._release_date_locator, text)

    @property
    def is_first_run(self):
        return self.wait_for_and_find_element(*self._first_run_locator).is_selected()

    def make_first_run(self):
        self.click_element(self._first_run_locator)

    @property
    def locales(self):
        return self.wait_for_and_find_elements(*self._locales_input_locator)[0]

    @locales.setter
    def locales(self, locales):
        self.set_bootstrap_select(
            self._locales_button_locator, self._locales_input_locator, locales
        )

    @property
    def countries(self):
        return self.wait_for_and_find_elements(*self._countries_input_locator)[0]

    @countries.setter
    def countries(self, text):
        self.set_bootstrap_select(
            self._countries_button_locator, self._countries_input_locator, [text]
        )

    @property
    def languages(self):
        return self.wait_for_and_find_elements(*self._languages_input_locator)[0]

    @languages.setter
    def languages(self, text):
        self.set_bootstrap_select(
            self._languages_button_locator, self._languages_input_locator, [text]
        )

    def wait_until_release_date_not_found(self):
        self.wait.until(EC.invisibility_of_element_located(self._release_date_locator))

    def wait_until_first_run_not_found(self):
        self.wait.until(EC.invisibility_of_element_located(self._first_run_locator))
