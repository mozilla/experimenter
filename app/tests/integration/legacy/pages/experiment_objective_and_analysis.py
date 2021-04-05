import random
import string

from pages.base import Base
from selenium.webdriver.common.by import By


class ObjectiveAndAnalysisPage(Base):

    URL_TEMPLATE = "{experiment_url}edit-objectives"

    _objectives_text_box_locator = (By.CSS_SELECTOR, "#id_objectives")
    _analysis_plan_text_box_locator = (By.CSS_SELECTOR, "#id_analysis")
    _survey_checkbox_no_locator = (By.CSS_SELECTOR, "#id_survey_required_0")
    _survey_checkbox_yes_locator = (By.CSS_SELECTOR, "#id_survey_required_1")
    _survey_url_box_locator = (By.CSS_SELECTOR, "#id_survey_urls")
    _survey_launch_text_box_locator = (By.CSS_SELECTOR, "#id_survey_instructions")

    _page_wait_locator = (By.CSS_SELECTOR, "body.page-edit-overview")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    @property
    def objectives_text_box(self):
        element = self.find_element(*self._objectives_text_box_locator)
        return element.text

    @objectives_text_box.setter
    def objectives_text_box(self, text=None):
        element = self.find_element(*self._objectives_text_box_locator)
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        element.send_keys(f"{text}-{random_chars}")
        return

    @property
    def analysis_text_box(self):
        element = self.find_element(*self._analysis_plan_text_box_locator)
        return element.text

    @analysis_text_box.setter
    def analysis_text_box(self, text=None):
        element = self.find_element(*self._analysis_plan_text_box_locator)
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        element.send_keys(f"{text}-{random_chars}")
        return

    @property
    def survey_required_checkbox(self):
        if self.find_element(*self._survey_checkbox_no_locator).get_attribute("checked"):
            return "No"
        if self.find_element(*self._survey_checkbox_yes_locator).get_attribute("checked"):
            return "Yes"
        raise ValueError("Unable to find survey value")

    @survey_required_checkbox.setter
    def survey_required_checkbox(self, text=None):
        if text == "No":
            self.find_element(*self._survey_checkbox_no_locator).click()
        elif text == "Yes":
            self.find_element(*self._survey_checkbox_yes_locator).click()
        else:
            raise SyntaxError("That option isn't a valid choice.")

    @property
    def survey_urls(self):
        element = self.find_element(*self._survey_url_box_locator)
        return element.text

    @survey_urls.setter
    def survey_urls(self, text=None):
        element = self.find_element(*self._survey_url_box_locator)
        element.send_keys(text)

    @property
    def survey_launch_instructions(self):
        element = self.find_element(*self._survey_launch_text_box_locator)
        return element.text

    @survey_launch_instructions.setter
    def survey_launch_instructions(self, text=None):
        element = self.find_element(*self._survey_launch_text_box_locator)
        element.send_keys(text)
