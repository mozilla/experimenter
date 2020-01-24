"""Representaion of the Timeline & Population Page."""

import random
import string

from selenium.webdriver.common.by import By
from pypom import Region

from pages.base import Base


class TimelineAndPopulationPage(Base):

    _firefox_channel_locator = (By.CSS_SELECTOR, "#id_firefox_channel")
    _firefox_min_version_locator = (By.CSS_SELECTOR, "#id_firefox_min_version")
    _firefox_max_version_locator = (By.CSS_SELECTOR, "#id_firefox_max_version")
    _locale_btn_locator = (
        By.XPATH,
        "/html/body/div[4]/div/div[1]/div[2]/div/form/div[9]/div[2]/div[1]/button",
    )
    _platform_locator = (By.CSS_SELECTOR, "#id_platform")
    _proposed_duration_locator = (By.CSS_SELECTOR, "#id_proposed_duration")
    _proposed_enrollment_locator = (By.CSS_SELECTOR, "#id_proposed_enrollment")
    _proposed_start_date_locator = (By.CSS_SELECTOR, "#id_proposed_start_date")
    _population_precentage_locator = (By.CSS_SELECTOR, "#id_population_percent")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(
                By.CSS_SELECTOR, "body.page-edit-timeline-and-population"
            )
        )
        return self

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
    def population_precentage(self):
        element = self.find_element(*self._population_precentage_locator)
        return element.get_attribute("value")

    @population_precentage.setter
    def population_precentage(self, text=None):
        element = self.find_element(*self._population_precentage_locator)
        element.clear()
        element.send_keys(text)

    @property
    def firefox_channel(self):
        element = self.find_element(*self._firefox_channel_locator)
        channels = element.find_elements(By.CSS_SELECTOR, "#id_firefox_channel > option")
        for item in channels:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @firefox_channel.setter
    def firefox_channel(self, channel=None):
        element = self.find_element(*self._firefox_channel_locator)
        channels = element.find_elements(By.CSS_SELECTOR, "#id_firefox_channel > option")
        for item in channels:
            if item.get_attribute("value") == channel:
                item.click()

    @property
    def firefox_min_version(self):
        element = self.find_element(*self._firefox_min_version_locator)
        versions = element.find_elements(
            By.CSS_SELECTOR, "#id_firefox_min_version > option"
        )
        for item in versions:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @firefox_min_version.setter
    def firefox_min_version(self, version=None):
        element = self.find_element(*self._firefox_min_version_locator)
        versions = element.find_elements(
            By.CSS_SELECTOR, "#id_firefox_min_version > option"
        )
        for item in versions:
            if item.get_attribute("value") == version:
                item.click()

    @property
    def firefox_max_version(self):
        element = self.find_element(*self._firefox_max_version_locator)
        versions = element.find_elements(
            By.CSS_SELECTOR, "#id_firefox_max_version > option"
        )
        for item in versions:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @firefox_max_version.setter
    def firefox_max_version(self, version=None):
        element = self.find_element(*self._firefox_max_version_locator)
        versions = element.find_elements(
            By.CSS_SELECTOR, "#id_firefox_max_version > option"
        )
        for item in versions:
            if item.get_attribute("value") == version:
                item.click()

    @property
    def locale(self):
        element = self.find_element(*self._locale_btn_locator)
        # scroll to element
        self.selenium.execute_script("arguments[0].scrollIntoView(true);", element)
        self.selenium.execute_script("arguments[0].click();", element)
        locales = self.selenium.find_elements(By.CSS_SELECTOR, "div.show:nth-child(3) a")
        for item in locales:
            if item.get_attribute("aria-selected") == "true":
                locale_text = item.find_element(By.CSS_SELECTOR, "span.text").text
                self.selenium.execute_script("arguments[0].click();", element)
                return locale_text

    @locale.setter
    def locale(self, locale=None):
        element = self.find_element(*self._locale_btn_locator)
        self.selenium.execute_script("arguments[0].click();", element)
        locales = self.selenium.find_elements(By.CSS_SELECTOR, "div.show:nth-child(3) a")
        for item in locales:
            if locale in item.find_element(By.CSS_SELECTOR, "span.text").text:
                self.selenium.execute_script("arguments[0].click();", item)
                break
        self.selenium.execute_script("arguments[0].click();", element)

    @property
    def platform(self):
        element = self.find_element(*self._platform_locator)
        platforms = element.find_elements(By.CSS_SELECTOR, "#id_platform > option")
        for item in platforms:
            if item.get_attribute("selected"):
                return item.get_attribute("value")

    @platform.setter
    def platform(self, platform=None):
        element = self.find_element(*self._platform_locator)
        platforms = element.find_elements(By.CSS_SELECTOR, "#id_platform > option")
        for item in platforms:
            if item.get_attribute("value") == platform:
                item.click()
