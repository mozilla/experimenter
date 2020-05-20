import random
import string

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from pages.base import Base


class ExperimentOverview(Base):

    URL_TEMPLATE = "{experiment_url}edit"

    _root_locator = (By.CSS_SELECTOR, ".form-group")

    _experiment_feature_bugzilla_url_locator = (
        By.CSS_SELECTOR,
        "#id_feature_bugzilla_url",
    )
    _engineering_owner_locator = (By.CSS_SELECTOR, "#id_engineering_owner")
    _experiment_owner_locator = (By.CSS_SELECTOR, "#id_owner > option")
    _analysis_owner_locator = (By.CSS_SELECTOR, "#id_analysis_owner > option")
    _experiment_public_description_locator = (By.CSS_SELECTOR, "#id_public_description")
    _experiment_public_description_locator = (By.CSS_SELECTOR, "#id_public_description")
    _experiment_public_name_locator = (By.CSS_SELECTOR, "#id_public_name")
    _experiment_related_experiments_locator = (
        By.CSS_SELECTOR,
        ".filter-option-inner-inner",
    )
    _experiment_related_work_url_locator = (By.CSS_SELECTOR, "#id_related_work")
    _experiment_type_locator = (By.CSS_SELECTOR, "#id_type")
    _related_experiments_dropdown = (By.CSS_SELECTOR, "ul.dropdown-menu > li > a")
    _page_wait_locator = (By.CSS_SELECTOR, "body.page-edit-overview")
    _name_locator = (By.CSS_SELECTOR, "#id_name")
    _short_description_locator = (By.CSS_SELECTOR, "#id_short_description")
    _ds_issue_url_locator = (By.CSS_SELECTOR, "#id_data_science_issue_url")
    _overview_name_locator = (By.CSS_SELECTOR, "#id_name")
    _overview_description_locator = (By.CSS_SELECTOR, "#id_short_description")
    _overview_ds_issue_url_locator = (By.CSS_SELECTOR, "#id_data_science_issue_url")
    _overview_data_science_owner_locator = (By.CSS_SELECTOR, "#id_analysis_owner")
    _save_btn_locator = (By.CSS_SELECTOR, "#save-btn")
    _save_and_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-btn")

    _page_wait_locator = (By.CSS_SELECTOR, "body.page-edit-overview")

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
    def name(self):
        element = self.find_element(*self._name_locator)
        return element.get_attribute("value")

    @name.setter
    def name(self, text=None):
        element = self.find_element(*self._name_locator)
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        element.send_keys(f"{text}-{random_chars}")
        return

    @property
    def short_description(self):
        element = self.find_element(*self._short_description_locator)
        return element.get_attribute("value")

    @short_description.setter
    def short_description(self, text=None):
        element = self.find_element(*self._short_description_locator)
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        element.send_keys(f"{text}-{random_chars}")
        return

    @property
    def ds_issue_url(self):
        element = self.find_element(*self._ds_issue_url_locator)
        return element.get_attribute("value")

    @ds_issue_url.setter
    def ds_issue_url(self, text=None):
        element = self.find_element(*self._ds_issue_url_locator)
        random_chars = "".join(random.choices(string.digits, k=6))
        element.send_keys(f"{text}{random_chars}")
        return

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
    def analysis_owner(self):
        options = self.find_elements(*self._analysis_owner_locator)
        for item in options:
            if item.get_property("selected"):
                return item.text

    @analysis_owner.setter
    def analysis_owner(self, owner=None):
        owners = self.find_elements(*self._analysis_owner_locator)
        for item in owners:
            if owner in item.text:
                item.click()
                return
        raise (Exception, "Owner selection not found")

    @property
    def engineering_owner(self):
        element = self.find_element(*self._engineering_owner_locator)
        return element.get_attribute("value")

    @engineering_owner.setter
    def engineering_owner(self, name=None):
        element = self.find_element(*self._engineering_owner_locator)
        element.send_keys(name)

    @property
    def public_name(self):
        element = self.find_element(*self._experiment_public_name_locator)
        return element.get_attribute("value")

    @public_name.setter
    def public_name(self, text=None):
        element = self.find_element(*self._experiment_public_name_locator)
        element.send_keys(text)

    @property
    def public_description(self):
        element = self.find_element(*self._experiment_public_description_locator)
        return element.get_attribute("value")

    @public_description.setter
    def public_description(self, text=None):
        element = self.find_element(*self._experiment_public_description_locator)
        element.send_keys(text)

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
            elements = self.find_elements(*self._related_experiments_dropdown)
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
        from pages.experiment_timeline_and_population import TimelineAndPopulationPage

        return TimelineAndPopulationPage(
            self.driver, self.base_url
        ).wait_for_page_to_load()
