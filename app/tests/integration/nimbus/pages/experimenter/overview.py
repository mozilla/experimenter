from nimbus.pages.experimenter.base import ExperimenterBase
from nimbus.pages.experimenter.branches import BranchesPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


class OverviewPage(ExperimenterBase):
    """Experiment Overview Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditOverview")
    _additional_link_root_locator = (By.CSS_SELECTOR, "#documentation-link")
    _additional_link_type_locator = (By.CSS_SELECTOR, "#documentation-link select")
    _additional_links_button_locator = (
        By.CSS_SELECTOR,
        "#documentation-links button.btn-outline-primary",
    )
    _public_description_locator = (By.CSS_SELECTOR, "#publicDescription")
    _risk_brand_locator = (By.CSS_SELECTOR, "#riskBrand-false")
    _risk_revenue_locator = (By.CSS_SELECTOR, "#riskRevenue-false")
    _risk_partner_locator = (By.CSS_SELECTOR, "#riskPartnerRelated-false")
    NEXT_PAGE = BranchesPage

    @property
    def public_description(self):
        return self.find_element(*self._public_description_locator).text

    @public_description.setter
    def public_description(self, text=None):
        name = self.find_element(*self._public_description_locator)
        name.send_keys(f"{text}")

    def select_risk_brand_false(self):
        el = self.find_element(*self._risk_brand_locator)
        el.click()

    def select_risk_revenue_false(self):
        el = self.find_element(*self._risk_revenue_locator)
        el.click()

    def select_risk_partner_false(self):
        el = self.find_element(*self._risk_partner_locator)
        el.click()

    @property
    def additional_links(self):
        el = self.find_element(*self._additional_link_type_locator)
        select = Select(el)
        return select.first_selected_option

    def set_additional_links(self, value=None, url="http://www.nimbus-rocks.com"):
        els = self.find_elements(*self._additional_link_root_locator)
        for item in els:
            if item.find_element(By.CSS_SELECTOR, "input").get_attribute("value") == "":
                item.find_element(By.CSS_SELECTOR, "input").send_keys(url)
                select = Select(item.find_element(By.CSS_SELECTOR, "select"))
                select.select_by_value(value)

    def add_additional_links(self):
        self.find_element(*self._additional_links_button_locator).click()
