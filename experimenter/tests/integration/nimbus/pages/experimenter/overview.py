from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.branches import BranchesPage


class OverviewPage(ExperimenterBase):
    """Experiment Overview Page."""

    PAGE_TITLE = "Overview Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#metrics-form")
    _additional_link_root_locator = (By.CSS_SELECTOR, "#documentation-links .form-group")
    _additional_link_input_locator = (
        By.CSS_SELECTOR,
        "#documentation-links .form-group input",
    )
    _additional_link_select_locator = (
        By.CSS_SELECTOR,
        "#documentation-links .form-group select",
    )
    _additional_links_button_locator = (
        By.CSS_SELECTOR,
        "#metrics-form button.btn.btn-outline-primary",
    )
    _public_description_locator = (By.CSS_SELECTOR, "#id_public_description")
    _risk_brand_locator = (By.CSS_SELECTOR, "#id_risk_brand_1")
    _risk_message_locator = (By.CSS_SELECTOR, "#id_risk_message_1")
    _risk_revenue_locator = (By.CSS_SELECTOR, "#id_risk_revenue_1")
    _risk_partner_locator = (By.CSS_SELECTOR, "#id_risk_partner_related_1")
    _projects_input_locator = (By.CSS_SELECTOR, "#id_projects")
    _projects_value_locator = (
        By.CSS_SELECTOR,
        "div[class*='multiValue'] > div:nth-child(1)",
    )
    _project_dropdown_locator = (By.CSS_SELECTOR, "#metrics-form .dropdown")
    NEXT_PAGE = BranchesPage

    @property
    def projects(self):
        return [
            element.text for element in self.find_elements(*self._projects_value_locator)
        ]

    @projects.setter
    def projects(self, text=None):
        self.wait_for_and_find_element(*self._project_dropdown_locator).click()
        el = self.wait_for_and_find_element(*self._projects_input_locator)
        select = Select(el)
        select.select_by_value(text)

    @property
    def public_description(self):
        return self.wait_for_and_find_element(*self._public_description_locator).text

    @public_description.setter
    def public_description(self, text=None):
        name = self.wait_for_and_find_element(*self._public_description_locator)
        name.send_keys(text)

    def select_risk_brand_false(self):
        el = self.wait_for_and_find_element(*self._risk_brand_locator)
        el.click()

    def select_risk_message_false(self):
        el = self.wait_for_and_find_element(*self._risk_message_locator)
        el.click()

    def select_risk_revenue_false(self):
        el = self.wait_for_and_find_element(*self._risk_revenue_locator)
        el.click()

    def select_risk_partner_false(self):
        el = self.wait_for_and_find_element(*self._risk_partner_locator)
        el.click()

    @property
    def additional_links(self):
        el = self.wait_for_and_find_element(*self._additional_link_type_locator)
        select = Select(el)
        return select.first_selected_option

    def set_additional_links(self, value=None, url="http://www.nimbus-rocks.com"):
        els = self.wait_for_and_find_elements(*self._additional_link_root_locator)
        for _ in els:
            try:
                self.wait_for_and_find_element(
                    By.CSS_SELECTOR, "#id_documentation_links-0-link"
                ).send_keys(url)
                select = Select(
                    self.wait_for_and_find_element(
                        By.CSS_SELECTOR, "#id_documentation_links-0-title"
                    )
                )
                select.select_by_value(value)
            except ElementNotInteractableException:
                continue

    def add_additional_links(self):
        self.wait_for_and_find_element(*self._additional_links_button_locator).click()
