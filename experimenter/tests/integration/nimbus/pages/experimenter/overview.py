from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.branches import BranchesPage


class OverviewPage(ExperimenterBase):
    """Experiment Overview Page."""

    PAGE_TITLE = "Overview Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#overview-form")
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
        "#overview-form button.btn.btn-outline-primary",
    )
    _public_description_locator = (By.CSS_SELECTOR, "#id_public_description")
    _risk_brand_locator = (By.CSS_SELECTOR, "#id_risk_brand_1")
    _risk_message_locator = (By.CSS_SELECTOR, "#id_risk_message_1")
    _risk_revenue_locator = (By.CSS_SELECTOR, "#id_risk_revenue_1")
    _risk_partner_locator = (By.CSS_SELECTOR, "#id_risk_partner_related_1")
    _tags_dropdown_locator = (By.CSS_SELECTOR, "#assignTagsDropdown")
    _tags_checkbox_locator = (By.CSS_SELECTOR, "input[name='tags']")
    _tag_label_locator = (By.CSS_SELECTOR, ".form-check-label")
    NEXT_PAGE = BranchesPage

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
    def tags(self):
        checkboxes = self.find_elements(*self._tags_checkbox_locator)
        return [cb.get_attribute("value") for cb in checkboxes if cb.is_selected()]

    def select_tag(self, tag_id):
        self.wait_for_and_find_element(*self._tags_dropdown_locator).click()
        checkbox = self.wait_for_and_find_element(By.CSS_SELECTOR, f"#tag-{tag_id}")
        if not checkbox.is_selected():
            checkbox.click()

    def select_first_available_tag(self):
        """Select the first available tag for testing."""
        self.wait_for_and_find_element(*self._tags_dropdown_locator).click()
        checkboxes = self.find_elements(*self._tags_checkbox_locator)
        if checkboxes:
            first_checkbox = checkboxes[0]
            if not first_checkbox.is_selected():
                first_checkbox.click()
            return first_checkbox.get_attribute("value")
        return None

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
