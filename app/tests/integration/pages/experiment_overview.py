import random
import string

from pages.base import Base
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


def get_random_chars():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def get_random_digits():
    return "".join(random.choices(string.digits, k=6))


class ExperimentOverview(Base):

    URL_TEMPLATE = "{experiment_url}edit"

    _page_wait_locator = (By.CSS_SELECTOR, "body.page-edit-overview")
    _root_locator = (By.CSS_SELECTOR, ".form-group")

    _experiment_type_locator = (By.CSS_SELECTOR, "#id_type")
    _experiment_owner_locator = (By.CSS_SELECTOR, "#id_owner")
    _experiment_public_name_locator = (By.CSS_SELECTOR, "#id_name")
    _experiment_public_description_locator = (By.CSS_SELECTOR, "#id_public_description")
    _experiment_internal_description_locator = (By.CSS_SELECTOR, "#id_short_description")
    _experiment_ds_issue_url_locator = (By.CSS_SELECTOR, "#id_data_science_issue_url")
    _experiment_analysis_owner_locator = (By.CSS_SELECTOR, "#id_analysis_owner > option")
    _experiment_engineering_owner_locator = (By.CSS_SELECTOR, "#id_engineering_owner")
    _experiment_feature_bugzilla_url_locator = (
        By.CSS_SELECTOR,
        "#id_feature_bugzilla_url",
    )
    _experiment_related_work_url_locator = (By.CSS_SELECTOR, "#id_related_work")
    _experiment_related_experiments_locator = (
        By.CSS_SELECTOR,
        ".filter-option-inner-inner",
    )
    _experiment_related_experiments_dropdown = (
        By.CSS_SELECTOR,
        "ul.dropdown-menu > li > a",
    )

    _experiment_related_work_url_locator = (By.CSS_SELECTOR, "#id_related_work")

    _save_btn_locator = (By.CSS_SELECTOR, "#save-btn")
    _save_and_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-btn")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    @property
    def experiment_type(self):
        options = self.find_element(*self._experiment_type_locator)
        options = options.find_elements_by_css_selector("option")
        for item in options:
            if item.get_property("selected"):
                return item.text

    @experiment_type.setter
    def experiment_type(self, exp_type=None):
        types = self.find_element(*self._experiment_type_locator)
        selector = Select(types)
        selector.select_by_visible_text(f"{exp_type}")

    @property
    def experiment_owner(self):
        options = self.find_elements(*self._experiment_owner_locator)
        for item in options:
            if item.get_property("selected"):
                return item.text

    @experiment_owner.setter
    def experiment_owner(self, owner=None):
        owners = self.find_elements(*self._experiment_owner_locator)
        for item in owners:
            if owner in item.text:
                item.click()
                return
        raise ValueError("Owner selection not found")

    @property
    def public_name(self):
        element = self.find_element(*self._experiment_public_name_locator)
        return element.get_attribute("value")

    @public_name.setter
    def public_name(self, text=None):
        element = self.find_element(*self._experiment_public_name_locator)
        random_chars = get_random_chars()
        element.send_keys(f"{text}-{random_chars}")
        return

    @property
    def public_description(self):
        element = self.find_element(*self._experiment_public_description_locator)
        return element.get_attribute("value")

    @public_description.setter
    def public_description(self, text=None):
        element = self.find_element(*self._experiment_public_description_locator)
        element.send_keys(text)

    @property
    def internal_description(self):
        element = self.find_element(*self._experiment_internal_description_locator)
        return element.get_attribute("value")

    @internal_description.setter
    def internal_description(self, text=None):
        element = self.find_element(*self._experiment_internal_description_locator)
        random_chars = get_random_chars()
        element.send_keys(f"{text}-{random_chars}")
        return

    @property
    def ds_issue_url(self):
        element = self.find_element(*self._experiment_ds_issue_url_locator)
        return element.get_attribute("value")

    @ds_issue_url.setter
    def ds_issue_url(self, text=None):
        # sometimes the ds_issue_url doesn't exist
        try:
            element = self.find_element(*self._experiment_ds_issue_url_locator)
            random_digits = get_random_digits()
            element.send_keys(f"{text}{random_digits}")
        except ElementNotInteractableException:
            return
        else:
            return

    @property
    def analysis_owner(self):
        options = self.find_elements(*self._experiment_analysis_owner_locator)
        for item in options:
            if item.get_property("selected"):
                return item.text

    @analysis_owner.setter
    def analysis_owner(self, owner=None):
        owners = self.find_elements(*self._experiment_analysis_owner_locator)
        for item in owners:
            if owner in item.text:
                item.click()
                return
        raise (Exception, "Owner selection not found")

    @property
    def engineering_owner(self):
        element = self.find_element(*self._experiment_engineering_owner_locator)
        return element.get_attribute("value")

    @engineering_owner.setter
    def engineering_owner(self, name=None):
        element = self.find_element(*self._experiment_engineering_owner_locator)
        element.send_keys(name)

    @property
    def feature_bugzilla_url(self):
        element = self.find_element(*self._experiment_feature_bugzilla_url_locator)
        return element.get_attribute("value")

    @feature_bugzilla_url.setter
    def feature_bugzilla_url(self, text=None):
        element = self.find_element(*self._experiment_feature_bugzilla_url_locator)
        element.send_keys(text)

    @property
    def related_work_urls(self):
        element = self.find_element(*self._experiment_related_work_url_locator)
        return element.get_attribute("value")

    @related_work_urls.setter
    def related_work_urls(self, text=None):
        element = self.find_element(*self._experiment_related_work_url_locator)
        element.send_keys(text)

    @property
    def related_experiments(self):
        element = self.find_element(*self._experiment_related_experiments_locator)
        return element.text

    @related_experiments.setter
    def related_experiments(self, experiment=None):
        dropdown = self.find_element(By.CSS_SELECTOR, ".dropdown-toggle")
        if type(experiment) is int:
            dropdown.click()
            elements = self.find_elements(*self._experiment_related_experiments_dropdown)
            elements[experiment].click()
            return
        for item in elements:
            if experiment in item.text:
                item.click()
                return
        raise ValueError("Owner selection not found")

    def save_btn(self):
        self.find_element(*self._save_btn_locator).click()
        from pages.experiment_detail import DetailPage

        return DetailPage(self.driver, self.base_url).wait_for_page_to_load()

    def save_and_continue_btn(self):
        self.find_element(*self._save_and_continue_btn_locator).click()
        from pages.experiment_timeline_and_population import (
            TimelineAndPopulationPage,
        )

        return TimelineAndPopulationPage(
            self.driver, self.base_url
        ).wait_for_page_to_load()
