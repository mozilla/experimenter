from nimbus.pages.remote_settings.base import RemoteSettingsBase
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Dashboard(RemoteSettingsBase):
    """Remote Settings Review Dashboard page."""

    _approve_button_locator = (By.CSS_SELECTOR, ".simple-review-buttons .btn-success")
    _reject_button_locator = (By.CSS_SELECTOR, ".simple-review-buttons .btn-danger")
    _reject_modal_comment_locator = (By.CSS_SELECTOR, ".modal textarea")
    _reject_modal_submit_locator = (By.CSS_SELECTOR, ".modal .btn-primary")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))
        return self

    def approve(self):
        self.wait_with_refresh(
            self._approve_button_locator, "Kinto Review: Unable to locate approve button"
        )
        self.find_element(*self._approve_button_locator).click()

    def reject(self):
        self.wait_with_refresh(
            self._reject_button_locator, "Kinto Review: Unable to locate reject button"
        )
        self.find_element(*self._reject_button_locator).click()

        self.wait.until(
            EC.presence_of_element_located(self._reject_modal_comment_locator)
        )
        el = self.find_element(*self._reject_modal_comment_locator)
        el.send_keys("Rejected")

        self.wait.until(EC.presence_of_element_located(self._reject_modal_submit_locator))
        self.find_element(*self._reject_modal_submit_locator).click()
