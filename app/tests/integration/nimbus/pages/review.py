from nimbus.pages.base import Base
from pypom import Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class ReviewPage(Base):
    """Experiment Review Page."""

    _root_locator = (By.CSS_SELECTOR, "#PageRequestReview")
    _approve_request_button_locator = (By.CSS_SELECTOR, "#approve-request-button")
    _experiment_status_icon_locator = (
        By.CSS_SELECTOR,
        ".header-experiment-status .boarder-primary",
    )
    _launch_without_preview_locator = (By.CSS_SELECTOR, "#launch-to-review-button")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._root_locator))
        return self

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

    def approve(self):
        el = self.find_element(*self._approve_request_button_locator)
        el.click()

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
