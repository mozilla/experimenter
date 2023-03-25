"""Representaion of the Timeline & Population Page."""

from pages.base import Base
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


class TimelineAndPopulationPage(Base):

    URL_TEMPLATE = "{experiment_url}edit-timeline-population"

    _rollout_playbook_locator = (By.CSS_SELECTOR, "#id_rollout_playbook")
    _firefox_channel_locator = (By.CSS_SELECTOR, "#id_firefox_channel")
    _firefox_channel_option_locator = (By.CSS_SELECTOR, "#id_firefox_channel > option")
    _firefox_min_version_locator = (By.CSS_SELECTOR, "#id_firefox_min_version")
    _firefox_min_version_option_locator = (
        By.CSS_SELECTOR,
        "#id_firefox_min_version > option",
    )
    _firefox_max_version_locator = (By.CSS_SELECTOR, "#id_firefox_max_version")
    _firefox_max_version_option_locator = (
        By.CSS_SELECTOR,
        "#id_firefox_max_version > option",
    )
    _platform_locator = (By.CSS_SELECTOR, "#id_platform")
    _platform_option_locator = (By.CSS_SELECTOR, "#id_platform > option")
    _proposed_duration_locator = (By.CSS_SELECTOR, "#id_proposed_duration")
    _proposed_enrollment_locator = (By.CSS_SELECTOR, "#id_proposed_enrollment")
    _proposed_start_date_locator = (By.CSS_SELECTOR, "#id_proposed_start_date")
    _population_percentage_locator = (By.CSS_SELECTOR, "#id_population_percent")
    _save_btn_locator = (By.CSS_SELECTOR, "button.mr-1")
    _page_wait_locator = (By.CSS_SELECTOR, ".page-edit-timeline-and-population")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    def save_btn(self):
        self.find_element(*self._save_btn_locator).click()

    @property
    def proposed_start_date(self):
        element = self.find_element(*self._proposed_start_date_locator)
        return element.get_attribute("value")

    @proposed_start_date.setter
    def proposed_start_date(self, text=None):
        element = self.find_element(*self._proposed_start_date_locator)
        element.send_keys(text)

    @property
    def proposed_experiment_duration(self):
        element = self.find_element(*self._proposed_duration_locator)
        return element.get_attribute("value")

    @proposed_experiment_duration.setter
    def proposed_experiment_duration(self, text=None):
        element = self.find_element(*self._proposed_duration_locator)
        element.send_keys(text)

    @property
    def proposed_enrollment_duration(self):
        element = self.find_element(*self._proposed_enrollment_locator)
        return element.get_attribute("value")

    @proposed_enrollment_duration.setter
    def proposed_enrollment_duration(self, text=None):
        element = self.find_element(*self._proposed_enrollment_locator)
        element.send_keys(text)

    @property
    def population_percentage(self):
        element = self.find_element(*self._population_percentage_locator)
        return element.get_attribute("value")

    @population_percentage.setter
    def population_percentage(self, text=None):
        element = self.find_element(*self._population_percentage_locator)
        element.clear()
        element.send_keys(text)

    @property
    def rollout_playbook(self):
        self.selenium.find_element(*self._rollout_playbook_locator).text

    @rollout_playbook.setter
    def rollout_playbook(self, item=None):
        element = self.selenium.find_element(*self._rollout_playbook_locator)
        selector = Select(element)
        selector.select_by_visible_text(f"{item}")

    @property
    def firefox_channel(self):
        element = self.find_element(*self._firefox_channel_locator)
        channels = element.find_elements(*self._firefox_channel_option_locator)
        for item in channels:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @firefox_channel.setter
    def firefox_channel(self, channel=None):
        element = self.find_element(*self._firefox_channel_locator)
        channels = element.find_elements(*self._firefox_channel_option_locator)
        for item in channels:
            if item.get_attribute("value") == channel:
                item.click()

    @property
    def firefox_min_version(self):
        element = self.find_element(*self._firefox_min_version_locator)
        versions = element.find_elements(*self._firefox_min_version_option_locator)
        for item in versions:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @firefox_min_version.setter
    def firefox_min_version(self, version=None):
        element = self.find_element(*self._firefox_min_version_locator)
        versions = element.find_elements(*self._firefox_min_version_option_locator)
        for item in versions:
            if item.get_attribute("value") == version:
                item.click()

    @property
    def firefox_max_version(self):
        element = self.find_element(*self._firefox_max_version_locator)
        versions = element.find_elements(*self._firefox_max_version_option_locator)
        for item in versions:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @firefox_max_version.setter
    def firefox_max_version(self, version=None):
        element = self.find_element(*self._firefox_max_version_locator)
        versions = element.find_elements(*self._firefox_max_version_option_locator)
        for item in versions:
            if item.get_attribute("value") == version:
                item.click()

    @property
    def platform(self):
        element = self.find_element(*self._platform_locator)
        platforms = element.find_elements(*self._platform_option_locator)
        for item in platforms:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @platform.setter
    def platform(self, platform=None):
        element = self.find_element(*self._platform_locator)
        platforms = element.find_elements(*self._platform_option_locator)
        for item in platforms:
            if item.get_attribute("value") == platform:
                item.click()
