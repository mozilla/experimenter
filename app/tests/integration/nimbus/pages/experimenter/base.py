from nimbus.pages.base import Base
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class ExperimenterBase(Base):
    """Experimenter Base page."""

    _save_btn_locator = (By.CSS_SELECTOR, "#save-button")
    _save_continue_btn_locator = (By.CSS_SELECTOR, "#save-and-continue-button")
    _sidebar_details_link = (By.CSS_SELECTOR, 'a[data-testid="nav-details"]')
    _sidebar_edit_branches_link = (By.CSS_SELECTOR, 'a[data-testid="nav-edit-branches"]')
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

    def navigate_to_details(self):
        # Avoid circular import
        from nimbus.pages.experimenter.summary_detail import SummaryDetailPage

        element = self.wait_for_and_find_element(
            self._sidebar_details_link, "details link"
        )
        element.click()
        return SummaryDetailPage(self.driver, self.base_url).wait_for_page_to_load()

    def navigate_to_branches(self):
        # Avoid circular import
        from nimbus.pages.experimenter.branches import BranchesPage

        element = self.wait_for_and_find_element(
            self._sidebar_edit_branches_link, "branches link"
        )
        element.click()
        return BranchesPage(self.driver, self.base_url).wait_for_page_to_load()
