from pages.base import Base
from pypom import Region
from selenium.webdriver.common.by import By


class RiskAndTestingPage(Base):

    URL_TEMPLATE = "{experiment_url}edit-risks"

    _risks_locator = (By.CSS_SELECTOR, ".form-group")
    _qa_status_box_locator = (By.CSS_SELECTOR, "#id_qa_status")
    _save_btn_locator = (By.CSS_SELECTOR, ".btn-primary")
    _page_wait_locator = (By.CSS_SELECTOR, ".page-edit-overview")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    @property
    def risks(self):
        elements = self.find_elements(*self._risks_locator)
        return [self.Risks(self, el) for el in elements]

    @property
    def qa_status_box(self):
        return self.find_element(*self._qa_status_box_locator).text

    @qa_status_box.setter
    def qa_status_box(self, text=None):
        box = self.find_element(*self._qa_status_box_locator)
        box.send_keys(text)

    def save_btn(self):
        self.find_element(*self._save_btn_locator).click()

        from pages.experiment_detail import DetailPage

        return DetailPage(self.driver, self.base_url).wait_for_page_to_load()

    class Risks(Region):

        _button_labels = (By.CSS_SELECTOR, ".radio label")
        _button_radio_button = (By.CSS_SELECTOR, "input")
        _risk_choices = (By.CSS_SELECTOR, "label strong")

        @property
        def risk_label(self):
            return self.find_element(*self._risk_choices).text

        def select_no(self):
            try:
                label = self.find_element(*self._button_labels)
                if label.text == "No":
                    label.find_element(*self._button_radio_button).click()
            except Exception:
                return

        def select_yes(self):
            label = self.find_element(*self._button_labels)
            if label.text == "Yes":
                label.find_element(*self._button_radio_button).click()
