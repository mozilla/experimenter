import random
import string

from selenium.webdriver.common.by import By

from pages.base import Base


class ExperimentOverview(Base):

    _root_locator = (By.CSS_SELECTOR, ".form-group")

    _page_wait_locator = (By.CSS_SELECTOR, "body.page-edit-overview")
    _overview_name_locator = (By.CSS_SELECTOR, "#id_name")
    _overview_description_locator = (By.CSS_SELECTOR, "#id_short_description")
    _overview_bugzilla_url_locator = (
        By.CSS_SELECTOR,
        "#id_data_science_bugzilla_url",
    )
    _save_and_continue_btn_locator = (By.CSS_SELECTOR, ".btn-primary:nth-child(2)")


    def fill_name(self, text=None):
        element = self.find_element(*self._overview_name_locator)
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        element.send_keys(f"{text}-{random_chars}")
        return

    def fill_short_description(self, text=None):
        element = self.find_element(*self._overview_description_locator)
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        element.send_keys(f"{text}-{random_chars}")
        return

    def fill_bugzilla_url(self, text=None):
        element = self.find_element(*self._overview_bugzilla_url_locator)
        random_chars = "".join(random.choices(string.digits, k=6))
        element.send_keys(f"{text}{random_chars}")
        return

    def save_and_continue_btn(self):
        self.find_element(*self._save_and_continue_btn_locator).click()
        from pages.experiment_population import PopulationPage

        return PopulationPage(
            self.driver, self.base_url
        ).wait_for_page_to_load()
