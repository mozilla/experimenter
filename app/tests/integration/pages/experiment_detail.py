"""Representaion of the Experiment Detail Page."""

from pages.base import Base
from pypom import Region
from selenium.webdriver.common.by import By


class DetailPage(Base):

    URL_TEMPLATE = "{experiment_url}"

    _begin_signoffs_btn_locator = (By.CSS_SELECTOR, ".proceed-status-color")
    _confirm_ship_btn_locator = (By.CSS_SELECTOR, ".proceed-status-color")
    _edit_branches_btn_locator = (By.CSS_SELECTOR, "#branches-edit-btn")
    _required_checklist_locator = (By.CSS_SELECTOR, ".checkbox")
    _save_signoffs_btn_locator = (By.CSS_SELECTOR, ".btn-success")
    _send_to_normandy_btn_locator = (By.CSS_SELECTOR, ".btn-danger")

    _page_wait_locator = (By.CSS_SELECTOR, "body.page-detail-view")

    def wait_for_page_to_load(self):
        self.wait.until(
            lambda _: self.find_element(*self._page_wait_locator).is_displayed()
        )
        return self

    @property
    def objective_section(self):
        return self.ObjectivesRegion(self)

    @property
    def analysis_section(self):
        return self.AnalysisRegion(self)

    @property
    def required_checklist_section(self):
        elements = self.find_elements(*self._required_checklist_locator)
        return [self.RequiredChecklist(self, el) for el in elements]

    @property
    def begin_signoffs_button(self):
        element = self.find_element(*self._begin_signoffs_btn_locator)
        assert "Begin Sign-Offs" in element.text
        return element

    @property
    def ready_to_ship_button(self):
        element = self.find_element(*self._confirm_ship_btn_locator)
        assert "Confirm Ready to Ship" in element.text
        return element

    @property
    def send_to_normandy_button(self):
        return self.find_element(*self._send_to_normandy_btn_locator)

    @property
    def save_sign_offs_button(self):
        return self.find_element(*self._save_signoffs_btn_locator)

    def click_edit(self):
        self.find_element(*self._edit_branches_btn_locator).click()

        from pages.experiment_design import DesignPage

        return DesignPage(self.driver, self.base_url).wait_for_page_to_load()

    class ObjectivesRegion(Region):

        _edit_btn_locator = (By.CSS_SELECTOR, "#objectives-edit-btn")
        _detail_locator = (By.CSS_SELECTOR, "#objectives-section-detail > p:nth-child(1)")

        def click_edit(self):
            self.find_element(*self._edit_btn_locator).click()

            from pages.experiment_objective_and_analysis import ObjectiveAndAnalysisPage

            return ObjectiveAndAnalysisPage(
                self.driver, self.page.base_url
            ).wait_for_page_to_load()

        @property
        def text(self):
            element = self.find_element(*self._detail_locator)
            return element.text

    class AnalysisRegion(Region):

        _edit_btn_locator = (By.CSS_SELECTOR, "#analysis-edit-btn")
        _detail_locator = (
            By.CSS_SELECTOR,
            "#analysis-section-detail > #analysis-content",
        )
        _survey_checkbox_locator = (
            By.CSS_SELECTOR,
            "#analysis-section-detail > #analysis-survey-required",
        )
        _survey_urls_locator = (
            By.CSS_SELECTOR,
            "#analysis-section-detail > #analysis-survey-urls",
        )
        _survey_launch_instructions_locator = (
            By.CSS_SELECTOR,
            "#analysis-section-detail > #analysis-survey-launch-instructions",
        )

        def click_edit(self):
            self.find_element(*self._edit_btn_locator).click()

            from pages.experiment_objective_and_analysis import ObjectiveAndAnalysisPage

            return ObjectiveAndAnalysisPage(
                self.driver, self.page.base_url
            ).wait_for_page_to_load()

        @property
        def text(self):
            element = self.find_element(*self._detail_locator)
            return element.text

        @property
        def survery_required(self):
            element = self.find_element(*self._survey_checkbox_locator)
            return element.text

        @property
        def survey_urls(self):
            element = self.find_element(*self._survey_urls_locator)
            return element.text

        @property
        def survey_launch_instructions(self):
            element = self.find_element(*self._survey_launch_instructions_locator)
            return element.get_attribute("textContent")

    class RequiredChecklist(Region):
        _checkbox_locator = (By.CSS_SELECTOR, "input")
        _checklist_item_label = (By.CSS_SELECTOR, "label")

        @property
        def label(self):
            return self.find_element(*self._checklist_item_label).text

        @property
        def checkbox(self):
            return self.find_element(*self._checkbox_locator)
