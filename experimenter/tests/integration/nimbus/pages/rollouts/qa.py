from selenium.webdriver.common.by import By

from nimbus.pages.rollouts.form_base import FormBase


class QASection(FormBase):
    """QA section of the rollout detail page."""

    PAGE_TITLE = "Rollout QA"
    CARD_ID = "qa"

    _status_locator = (By.ID, "id_qa_status")
    _comment_locator = (By.ID, "id_qa_comment")
    _displayed_status_locator = (By.ID, "rollout-qa-status")
    _displayed_comment_locator = (By.ID, "rollout-qa-comment")

    @property
    def status(self):
        return self.get_select(self._status_locator).get_attribute("value")

    @status.setter
    def status(self, value):
        self.set_select(self._status_locator, value)

    @property
    def comment(self):
        return self.get_input(self._comment_locator).get_attribute("value")

    @comment.setter
    def comment(self, value):
        self.set_input(self._comment_locator, value)

    @property
    def displayed_status(self):
        return self._wait_present(self._displayed_status_locator).text

    @property
    def displayed_comment(self):
        return self._wait_present(self._displayed_comment_locator).text
