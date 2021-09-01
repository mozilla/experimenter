import time

from nimbus.pages.base import Base
from pypom import Region
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class SummaryPage(Base):
    """Experiment Summary Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageSummary")
    _approve_request_button_locator = (By.CSS_SELECTOR, "#approve-request-button")
    _launch_without_preview_locator = (By.CSS_SELECTOR, "#launch-to-review-button")
    _rejected_text_alert_locator = (By.CSS_SELECTOR, "#PageSummary .alert-warning")
    _timeout_alert_locator = (By.CSS_SELECTOR, ".alert-danger")
    _experiment_status_icon_locator = (
        By.CSS_SELECTOR,
        ".header-experiment-status .border-primary",
    )
    _end_experiment_button_locator = (By.CSS_SELECTOR, ".end-experiment-start-button")
    _confirm_end_button_locator = (By.CSS_SELECTOR, ".end-experiment-confirm-button")
    _archive_button_locator = (By.CSS_SELECTOR, 'button[data-testid="action-archive"]')
    _archive_label_locator = (
        By.CSS_SELECTOR,
        'span[data-testid="header-experiment-status-archived"]',
    )

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._page_wait_locator))
        return self

    def wait_for_archive_label_visible(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._archive_label_locator),
            message="Summary Page: could not find archive label",
        )

    def wait_for_archive_label_not_visible(self):
        self.wait.until_not(
            EC.presence_of_all_elements_located(self._archive_label_locator),
            message="Summary Page: archive label still present",
        )

    @property
    def experiment_status(self):
        el = self.find_element(*self._experiment_status_icon_locator)
        return el.text

    @property
    def launch_without_preview(self):
        return self.find_element(*self._launch_without_preview_locator)

    @property
    def request_review(self):
        return self.RequestReview(self)

    def approve(self, timeout=45):
        for _ in range(timeout):
            try:
                el = self.find_element(*self._approve_request_button_locator)
                el.click()
                break
            except NoSuchElementException:
                time.sleep(2)
                continue
        else:
            raise AssertionError("Approve button was never shown")

    def end_experiment(self, action="End"):
        el = self.find_element(*self._end_experiment_button_locator)
        el.click()
        if action == "End":
            self.wait.until(
                EC.presence_of_element_located(self._confirm_end_button_locator)
            )
            el = self.find_element(*self._confirm_end_button_locator)
            el.click()
        else:
            pass

    @property
    def rejected_text(self):
        el = self.find_element(*self._rejected_text_alert_locator)
        return el.is_displayed()

    @property
    def timeout_text(self):
        return self.selenium.find_element(*self._timeout_alert_locator)

    class RequestReview(Region):
        _root_locator = (By.CSS_SELECTOR, "#request-launch-alert")
        _checkbox0_locator = (By.CSS_SELECTOR, "#checkbox-0")
        _checkbox1_locator = (By.CSS_SELECTOR, "#checkbox-1")
        _request_launch_locator = (By.CSS_SELECTOR, "#request-launch-button")

        def click_launch_checkboxes(self):
            self.find_element(*self._checkbox0_locator).click()
            self.find_element(*self._checkbox1_locator).click()

        @property
        def request_launch_button(self):
            return self.find_element(*self._request_launch_locator)

    @property
    def archive_button(self):
        return self.find_element(*self._archive_button_locator)

    @property
    def archive_label(self):
        return self.find_element(*self._archive_label_locator)
