from selenium.webdriver.common.by import By

from nimbus.pages.rollouts.form_base import FormBase


class SignoffSection(FormBase):
    """Sign-Offs section of the rollout detail page."""

    PAGE_TITLE = "Rollout Sign-Offs"
    CARD_ID = "signoff"

    _qa_signoff_locator = (By.ID, "id_qa_signoff")
    _vp_signoff_locator = (By.ID, "id_vp_signoff")
    _legal_signoff_locator = (By.ID, "id_legal_signoff")

    _displayed_qa_signoff_locator = (By.ID, "rollout-signoff-qa")
    _displayed_vp_signoff_locator = (By.ID, "rollout-signoff-vp")
    _displayed_legal_signoff_locator = (By.ID, "rollout-signoff-legal")

    def _get_signoff(self, locator):
        return self._wait_present(locator).is_selected()

    def _set_signoff(self, locator, value):
        checkbox = self._wait_present(locator)
        if checkbox.is_selected() != value:
            self.click_element(locator)

    def _get_displayed_signoff(self, locator):
        return "fa-check" in self._wait_present(locator).get_attribute("class").split()

    @property
    def qa_signoff(self):
        return self._get_signoff(self._qa_signoff_locator)

    @qa_signoff.setter
    def qa_signoff(self, value):
        self._set_signoff(self._qa_signoff_locator, value)

    @property
    def vp_signoff(self):
        return self._get_signoff(self._vp_signoff_locator)

    @vp_signoff.setter
    def vp_signoff(self, value):
        self._set_signoff(self._vp_signoff_locator, value)

    @property
    def legal_signoff(self):
        return self._get_signoff(self._legal_signoff_locator)

    @legal_signoff.setter
    def legal_signoff(self, value):
        self._set_signoff(self._legal_signoff_locator, value)

    @property
    def displayed_qa_signoff(self):
        return self._get_displayed_signoff(self._displayed_qa_signoff_locator)

    @property
    def displayed_vp_signoff(self):
        return self._get_displayed_signoff(self._displayed_vp_signoff_locator)

    @property
    def displayed_legal_signoff(self):
        return self._get_displayed_signoff(self._displayed_legal_signoff_locator)
