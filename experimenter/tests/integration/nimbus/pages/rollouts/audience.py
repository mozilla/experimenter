from selenium.webdriver.common.by import By

from nimbus.pages.rollouts.form_base import FormBase


class AudienceSection(FormBase):
    """Audience section of the rollout detail page."""

    PAGE_TITLE = "Rollout Audience"
    CARD_ID = "audience"

    _channel_locator = (By.ID, "id_channel")
    _channels_button_locator = (By.CSS_SELECTOR, "button[data-id='id_channels']")
    _channels_search_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_channels'] + .dropdown-menu input",
    )
    _min_version_locator = (By.ID, "id_firefox_min_version")
    _max_version_locator = (By.ID, "id_firefox_max_version")
    _countries_button_locator = (By.CSS_SELECTOR, "button[data-id='id_countries']")
    _countries_search_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_countries'] + .dropdown-menu input",
    )
    _locales_button_locator = (By.CSS_SELECTOR, "button[data-id='id_locales']")
    _locales_search_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_locales'] + .dropdown-menu input",
    )
    _languages_button_locator = (By.CSS_SELECTOR, "button[data-id='id_languages']")
    _languages_search_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_languages'] + .dropdown-menu input",
    )
    _targeting_button_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_targeting_config_slug']",
    )
    _targeting_search_locator = (
        By.CSS_SELECTOR,
        "button[data-id='id_targeting_config_slug'] + .dropdown-menu input",
    )
    _sticky_locators = (
        (By.ID, "id_is_sticky_0"),
        (By.ID, "id_is_sticky_1"),
    )
    _localized_locator = (By.ID, "id_is_localized")

    _displayed_channel_locator = (By.ID, "rollout-audience-channel")
    _displayed_min_version_locator = (By.ID, "rollout-audience-min-version")
    _displayed_max_version_locator = (By.ID, "rollout-audience-max-version")
    _displayed_countries_locator = (By.ID, "rollout-audience-countries")
    _displayed_targeting_locator = (By.ID, "rollout-audience-targeting")
    _displayed_sticky_locator = (By.ID, "rollout-audience-sticky")
    _displayed_localized_locator = (By.ID, "rollout-audience-localized")

    def _set_checkbox(self, locator, value):
        checkbox = self._wait_present(locator)
        if checkbox.is_selected() != value:
            self.click_element(locator)

    def _get_displayed_boolean(self, locator):
        return "fa-check" in self._wait_present(locator).get_attribute("class").split()

    @property
    def channel(self):
        return self.get_select(self._channel_locator).get_attribute("value")

    @channel.setter
    def channel(self, value):
        self.set_select_by_text(self._channel_locator, value)

    @property
    def channels(self):
        return self._wait_present(self._channels_button_locator).text

    @channels.setter
    def channels(self, values):
        self.set_bootstrap_select(
            self._channels_button_locator,
            self._channels_search_locator,
            values,
        )

    @property
    def min_version(self):
        return self.get_select(self._min_version_locator).get_attribute("value")

    @min_version.setter
    def min_version(self, value):
        self.set_select(self._min_version_locator, value)

    @property
    def max_version(self):
        return self.get_select(self._max_version_locator).get_attribute("value")

    @max_version.setter
    def max_version(self, value):
        self.set_select(self._max_version_locator, value)

    @property
    def countries(self):
        return self._wait_present(self._countries_button_locator).text

    @countries.setter
    def countries(self, values):
        self.set_bootstrap_select(
            self._countries_button_locator,
            self._countries_search_locator,
            values,
        )

    @property
    def locales(self):
        return self._wait_present(self._locales_button_locator).text

    @locales.setter
    def locales(self, values):
        self.set_bootstrap_select(
            self._locales_button_locator,
            self._locales_search_locator,
            values,
        )

    @property
    def languages(self):
        return self._wait_present(self._languages_button_locator).text

    @languages.setter
    def languages(self, values):
        self.set_bootstrap_select(
            self._languages_button_locator,
            self._languages_search_locator,
            values,
        )

    @property
    def targeting(self):
        return self._wait_present(self._targeting_button_locator).text

    @targeting.setter
    def targeting(self, value):
        self.set_bootstrap_select(
            self._targeting_button_locator,
            self._targeting_search_locator,
            [value],
        )

    @property
    def is_sticky(self):
        return self._wait_present(self._sticky_locators[0]).is_selected()

    @is_sticky.setter
    def is_sticky(self, value):
        self.click_element(self._sticky_locators[0 if value else 1])

    @property
    def is_localized(self):
        return self._wait_present(self._localized_locator).is_selected()

    @is_localized.setter
    def is_localized(self, value):
        self._set_checkbox(self._localized_locator, value)

    @property
    def displayed_channel(self):
        return self._wait_present(self._displayed_channel_locator).text

    @property
    def displayed_min_version(self):
        return self._wait_present(self._displayed_min_version_locator).text

    @property
    def displayed_max_version(self):
        return self._wait_present(self._displayed_max_version_locator).text

    @property
    def displayed_countries(self):
        return self._wait_present(self._displayed_countries_locator).text

    @property
    def displayed_targeting(self):
        return self._wait_present(self._displayed_targeting_locator).text

    @property
    def displayed_is_sticky(self):
        return self._get_displayed_boolean(self._displayed_sticky_locator)

    @property
    def displayed_is_localized(self):
        return self._get_displayed_boolean(self._displayed_localized_locator)
