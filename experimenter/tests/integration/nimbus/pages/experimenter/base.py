from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.base import Base


class ExperimenterBase(Base):
    """Experimenter Base page."""

    _save_btn_locator = (By.CSS_SELECTOR, "#save-button")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-button")
    _sidebar_summary_link = (By.CSS_SELECTOR, 'a[data-testid="nav-summary"]')
    _sidebar_edit_overview_link = (By.CSS_SELECTOR, 'a[data-testid="nav-edit-overview"]')
    _sidebar_edit_branches_link = (By.CSS_SELECTOR, 'a[data-testid="nav-edit-branches"]')
    _sidebar_edit_audience_link = (By.CSS_SELECTOR, 'a[data-testid="nav-edit-audience"]')

    NEXT_PAGE = None
    PAGE_TITLE = ""

    def wait_for_locator(self, locator, description):
        self.wait.until(
            EC.presence_of_all_elements_located(locator),
            message=f"{self.PAGE_TITLE}: could not find {description}",
        )

    def wait_for_and_find_element(self, locator, description):
        self.wait_for_locator(locator, description)
        return self.find_element(*locator)

    def wait_for_and_find_elements(self, locator, description):
        self.wait_for_locator(locator, description)
        return self.find_elements(*locator)

    def save_and_continue(self):
        element = self.wait_for_and_find_element(
            self._save_continue_btn_locator, "save and continue button"
        )
        element.click()
        return self.NEXT_PAGE(self.driver, self.base_url).wait_for_page_to_load()

    def save(self):
        element = self.wait_for_and_find_element(self._save_btn_locator, "save button")
        element.click()

    def navigate_to_summary(self):
        # Avoid circular import
        from nimbus.pages.experimenter.summary import SummaryPage

        element = self.wait_for_and_find_element(
            self._sidebar_summary_link, "summary link"
        )
        element.click()
        return SummaryPage(self.driver, self.base_url).wait_for_page_to_load()

    def navigate_to_overview(self):
        # Avoid circular import
        from nimbus.pages.experimenter.overview import OverviewPage

        element = self.wait_for_and_find_element(
            self._sidebar_edit_overview_link, "overview link"
        )
        element.click()
        return OverviewPage(self.driver, self.base_url).wait_for_page_to_load()

    def navigate_to_branches(self):
        # Avoid circular import
        from nimbus.pages.experimenter.branches import BranchesPage

        element = self.wait_for_and_find_element(
            self._sidebar_edit_branches_link, "branches link"
        )
        element.click()
        return BranchesPage(self.driver, self.base_url).wait_for_page_to_load()

    def navigate_to_audience(self):
        # Avoid circular import
        from nimbus.pages.experimenter.audience import AudiencePage

        element = self.wait_for_and_find_element(
            self._sidebar_edit_audience_link, "audience link"
        )
        element.click()
        return AudiencePage(self.driver, self.base_url).wait_for_page_to_load()
