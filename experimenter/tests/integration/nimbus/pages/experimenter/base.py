from selenium.webdriver.common.by import By

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

    def save_and_continue(self):
        element = self.wait_for_and_find_element(
            *self._save_continue_btn_locator, "save and continue button"
        )
        element.click()

        # Wait for next page to load after save and continue before proceeding
        self.wait_for_locator(self.NEXT_PAGE._page_wait_locator)

        return self.NEXT_PAGE(self.driver, self.base_url).wait_for_page_to_load()

    def save(self):
        element = self.wait_for_and_find_element(*self._save_btn_locator, "save button")
        element.click()

    def navigate_to_summary(self):
        # Avoid circular import
        from nimbus.pages.experimenter.summary import SummaryPage

        element = self.wait_for_and_find_element(
            *self._sidebar_summary_link, "summary link"
        )
        element.click()
        return SummaryPage(self.driver, self.base_url).wait_for_page_to_load()

    def navigate_to_overview(self):
        # Avoid circular import
        from nimbus.pages.experimenter.overview import OverviewPage

        element = self.wait_for_and_find_element(
            *self._sidebar_edit_overview_link, "overview link"
        )
        element.click()
        return OverviewPage(self.driver, self.base_url).wait_for_page_to_load()

    def navigate_to_branches(self):
        # Avoid circular import
        from nimbus.pages.experimenter.branches import BranchesPage

        element = self.wait_for_and_find_element(
            *self._sidebar_edit_branches_link, "branches link"
        )
        element.click()
        return BranchesPage(self.driver, self.base_url).wait_for_page_to_load()

    def navigate_to_audience(self):
        # Avoid circular import
        from nimbus.pages.experimenter.audience import AudiencePage

        element = self.wait_for_and_find_element(
            *self._sidebar_edit_audience_link, "audience link"
        )
        element.click()
        return AudiencePage(self.driver, self.base_url).wait_for_page_to_load()
