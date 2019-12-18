"""Representaion of the Experiment Detail Page."""

import random
import string

from selenium.webdriver.common.by import By
from pypom import Region

from pages.base import Base


class DetailPage(Base):

    _edit_branches_btn_locator = (By.CSS_SELECTOR, "#branches-edit-btn")

    _page_wait_locator = (By.CSS_SELECTOR, "body.page-detail-view")

    @property
    def objective_section(self):
        return self.ObjectivesRegion(self)

    @property
    def analysis_section(self):
        return self.AnalysisRegion(self)

    def click_edit(self):
        self.find_element(*self._edit_branches_btn_locator).click()

        from pages.experiment_design import DesignPage

        return DesignPage(self.driver, self.base_url).wait_for_page_to_load()

    class ObjectivesRegion(Region):

        _edit_btn_locator = (By.CSS_SELECTOR, "#objectives-edit-btn")
        _detail_locator = (
            By.CSS_SELECTOR,
            "#objectives-section-detail > p:nth-child(1)",
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

    class AnalysisRegion(Region):

        _edit_btn_locator = (By.CSS_SELECTOR, "#analysis-edit-btn")
        _detail_locator = (By.CSS_SELECTOR, "#analysis-section-detail > p:nth-child(2)")
        _survey_checkbox_locator = (
            By.CSS_SELECTOR,
            "#analysis-section-detail > strong > span",
        )
        _survey_urls_locator = (
            By.CSS_SELECTOR,
            "#analysis-section-detail > p:nth-child(6)",
        )
        _survey_launch_instructions_locator = (
            By.CSS_SELECTOR,
            "#analysis-section-detail > p:nth-child(8)",
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
            return element.text
