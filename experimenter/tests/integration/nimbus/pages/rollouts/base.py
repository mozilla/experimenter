from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.base import Base


class RolloutBase(Base):
    """Base for rollout-level actions on the rollout detail page."""

    PAGE_TITLE = "Rollout Detail Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#RolloutSummary")
    _actions_dropdown_locator = (By.ID, "rollout-actions-dropdown")
    _clone_button_locator = (By.ID, "rollout-clone-button")
    _archive_button_locator = (By.ID, "rollout-archive-button")
    _clone_modal_locator = (By.ID, "cloneModal")
    _clone_name_locator = (By.ID, "clone-name")
    _clone_submit_locator = (By.CSS_SELECTOR, "#cloneForm button[type='submit']")
    _header_name_locator = (By.ID, "experiment-header-name")
    _archived_badge_locator = (By.ID, "archive-badge")
    _live_badge_locator = (By.ID, "rollout-live-badge")
    _preview_button_locator = (By.ID, "rollout-preview-btn")
    _preview_section_locator = (By.ID, "rollout-preview-section")
    _request_enrollment_button_locator = (
        By.ID,
        "rollout-request-enrollment-btn",
    )
    _review_approve_button_locator = (By.ID, "rollout-review-approve-btn")
    _disable_button_locator = (By.ID, "rollout-disable-btn")
    _resume_button_locator = (By.ID, "rollout-resume-btn")
    _next_phase_button_locator = (By.ID, "rollout-next-phase-btn")

    def _click_and_wait_for_refresh(self, locator, action):
        page = self._wait_present(self._page_wait_locator)
        self.click_element(locator)
        self.wait.until(
            EC.staleness_of(page),
            message=f"{self.PAGE_TITLE}: {action} did not refresh the page",
        )
        return self.wait_for_page_to_load()

    def _click_transition_and_wait_for_refresh(self, locator, action):
        self.wait_with_refresh_until_enabled(
            locator,
            f"{self.PAGE_TITLE}: {action} button never became enabled",
        )
        return self._click_and_wait_for_refresh(locator, action)

    def open_actions_dropdown(self):
        self.click_element(self._actions_dropdown_locator)
        return self

    def open_clone_modal(self):
        self.open_actions_dropdown()
        self.click_element(self._clone_button_locator)
        self.wait.until(
            EC.visibility_of_element_located(self._clone_modal_locator),
            message=f"{self.PAGE_TITLE}: clone modal did not open",
        )
        return self

    @property
    def clone_name(self):
        return self.get_input(self._clone_name_locator).get_attribute("value")

    @clone_name.setter
    def clone_name(self, value):
        self.set_input(self._clone_name_locator, value)

    def submit_clone(self):
        self.click_and_wait_for_navigation(self._clone_submit_locator)
        return self

    @property
    def header_name(self):
        return self._wait_present(self._header_name_locator).text

    @property
    def is_archived(self):
        self.wait_for_htmx()
        return bool(self.selenium.find_elements(*self._archived_badge_locator))

    def toggle_archive(self):
        self.open_actions_dropdown()
        return self._click_and_wait_for_refresh(
            self._archive_button_locator,
            "archive action",
        )

    def transition_to_preview(self):
        return self._click_transition_and_wait_for_refresh(
            self._preview_button_locator,
            "preview transition",
        )

    @property
    def is_in_preview(self):
        self.wait_for_htmx()
        return bool(self.selenium.find_elements(*self._preview_section_locator))

    def request_enrollment(self):
        return self._click_transition_and_wait_for_refresh(
            self._request_enrollment_button_locator,
            "enrollment request",
        )

    def approve_review(self):
        return self._click_transition_and_wait_for_refresh(
            self._review_approve_button_locator,
            "review approval",
        )

    def wait_for_live_status(self):
        self.wait_with_refresh_and_assert(
            self._live_badge_locator,
            "Live",
            f"{self.PAGE_TITLE}: rollout did not reach live status",
        )
        return self

    def request_disable(self):
        return self._click_transition_and_wait_for_refresh(
            self._disable_button_locator,
            "disable request",
        )

    def request_reenable(self):
        return self._click_transition_and_wait_for_refresh(
            self._resume_button_locator,
            "re-enable request",
        )

    def request_phase_advance(self):
        return self._click_transition_and_wait_for_refresh(
            self._next_phase_button_locator,
            "phase advance request",
        )

    def wait_for_disabled_status(self):
        self.wait_with_refresh_until_enabled(
            self._resume_button_locator,
            f"{self.PAGE_TITLE}: rollout did not reach disabled status",
        )
        return self

    def wait_for_rollout_phase(self, phase_number):
        locator = (
            By.CSS_SELECTOR,
            f'#sidebar-rollout [aria-label="Phase {phase_number} progress"]',
        )
        self.wait_with_refresh(
            locator,
            f"{self.PAGE_TITLE}: rollout did not reach phase {phase_number}",
        )
        return self
