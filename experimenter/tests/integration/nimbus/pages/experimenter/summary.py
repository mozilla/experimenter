import random
import string

from pypom import Region
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.base import Base
from nimbus.pages.experimenter.base import ExperimenterBase


class SummaryPage(ExperimenterBase):
    """Experiment Summary Page."""

    PAGE_TITLE = "Summary Page"

    _page_wait_locator = (By.CSS_SELECTOR, "#PageSummary")
    _promote_rollout_locator = (By.CSS_SELECTOR, 'button[data-testid="promote-rollout"]')
    _header_slug = (By.CSS_SELECTOR, "#experiment-slug")
    _approve_request_button_locator = (By.CSS_SELECTOR, "#review-controls .btn-success")
    _reject_request_button_locator = (By.CSS_SELECTOR, "#reject-button")
    _reject_input_text_locator = (
        By.CSS_SELECTOR,
        "#changelog_message",
    )
    _reject_input_text_submit_locator = (By.CSS_SELECTOR, "#submit-rejection-button")
    _rejection_notice_locator = (By.CSS_SELECTOR, "#rejection-reason")
    _launch_to_preview_locator = (By.CSS_SELECTOR, "#draft-to-preview-button")
    _launch_without_preview_locator = (By.CSS_SELECTOR, "#draft-to-review-button")
    _rejected_text_alert_locator = (By.CSS_SELECTOR, '[data-testid="rejection-notice"]')
    _timeout_alert_locator = (By.CSS_SELECTOR, "#rejection-message")
    _status_live_locator = (By.CSS_SELECTOR, "#experiment-timeline .bg-primary strong")
    _status_preview_locator = (By.CSS_SELECTOR, ".status-Preview.border-primary")
    _status_complete_locator = (
        By.CSS_SELECTOR,
        "#experiment-timeline .bg-primary strong",
    )
    _update_request_locator = (By.CSS_SELECTOR, "#request-update-button")
    _experiment_status_icon_locator = (
        By.CSS_SELECTOR,
        ".header-experiment-status .border-primary",
    )
    _end_experiment_button_locator = (By.CSS_SELECTOR, "#end-experiment")
    _archive_button_locator = (By.CSS_SELECTOR, 'button[data-testid="nav-edit-archive"]')
    _archive_label_locator = (
        By.CSS_SELECTOR,
        "#archive-badge",
    )
    _clone_action_locator = (By.CSS_SELECTOR, 'a[data-testid="nav-edit-clone"]')
    _clone_name_field_locator = (
        By.CSS_SELECTOR,
        "#clone-name",
    )
    _clone_save_locator = (By.CSS_SELECTOR, "#cloneForm .btn-primary")
    _clone_parent_locator = (By.CSS_SELECTOR, 'a[data-testid="experiment-parent"]')
    _branch_screenshot_description_locator = (
        By.CSS_SELECTOR,
        'figure[data-testid="branch-screenshot"] figcaption',
    )
    _branch_screenshot_image_locator = (
        By.CSS_SELECTOR,
        'figure[data-testid="branch-screenshot"] img',
    )
    _takeaways_edit_button = (By.CSS_SELECTOR, 'a[data-testid="edit-takeaways"]')
    _takeaways_save_button = (
        By.CSS_SELECTOR,
        'button[data-testid="takeaways-edit-save"]',
    )
    _takeaways_recommendation_field = (
        By.CSS_SELECTOR,
        'form[data-testid="FormTakeaways"] input[name="conclusionRecommendations"]',
    )
    _takeaways_summary_field = (
        By.CSS_SELECTOR,
        "#takeawaysSummary",
    )
    _takeaways_summary_text = (
        By.CSS_SELECTOR,
        "#takeawaysSummaryText",
    )
    _takeaways_recommendation_badge = (
        By.CSS_SELECTOR,
        'span[data-testid="conclusion-recommendation-status"]',
    )
    _audience_section_locator = (
        By.CSS_SELECTOR,
        "#audience",
    )
    _audience_is_first_run_locator = (
        By.CSS_SELECTOR,
        '[data-testid="experiment-is-first-run"]',
    )
    _audience_proposed_release_date_locator = (
        By.CSS_SELECTOR,
        '[data-testid="experiment-release-date"]',
    )
    _timeline_locator = (
        By.CSS_SELECTOR,
        "#experiment-timeline",
    )
    _timeline_proposed_release_date_locator = (
        By.CSS_SELECTOR,
        '[data-testid="label-release-date"]',
    )
    _promote_to_rollout_form_locator = (By.CSS_SELECTOR, "#promoteToRolloutForm-control")
    _promote_to_rollout_name_locator = (By.CSS_SELECTOR, "#promote-control-name")
    _promote_to_rollout_save_locator = (
        By.CSS_SELECTOR,
        "#promoteToRolloutForm-control .btn-primary",
    )

    def wait_for_archive_label_visible(self):
        self.wait_with_refresh(
            self._archive_label_locator,
            message="Summary Page: could not find archive label",
        )

    def wait_for_archive_label_not_visible(self):
        self.wait.until_not(
            EC.presence_of_all_elements_located(self._archive_label_locator),
            message="Summary Page: archive label still present",
        )

    def wait_for_live_status(self):
        self.wait_with_refresh_and_assert(
            self._status_live_locator,
            "Enrollment",
            "Summary Page: Unable to find live status",
        )

    def wait_for_preview_status(self):
        self.wait_with_refresh(
            self._status_preview_locator, "Summary Page: Unable to find preview status"
        )

    def wait_for_complete_status(self):
        self.wait_with_refresh_and_assert(
            self._status_complete_locator,
            "Complete",
            "Summary Page: Unable to find complete status",
        )

    def wait_for_rejected_alert(self):
        self.wait_with_refresh(
            self._rejected_text_alert_locator,
            "Summary Page: Unable to find rejected alert",
        )

    def wait_for_timeout_alert(self):
        self.wait_with_refresh(
            self._timeout_alert_locator, "Summary Page: Unable to find timeout alert"
        )

    def wait_for_clone_parent_link_visible(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._clone_parent_locator),
            message="Summary Page: could not find clone parent",
        )

    def wait_for_update_request_visible(self):
        self.wait_with_refresh(
            self._update_request_locator, "Summary Page: Unable to find update request"
        )

    def wait_for_rejection_reason_text_input_visible(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._reject_input_text_locator),
            message="Summary Page: could not find rejection reason text input",
        )

    def wait_for_rejection_notice_visible(self):
        self.wait_with_refresh(
            self._rejection_notice_locator,
            "Summary Page: could not find rejection notice",
        )

    def set_rejection_reason(self):
        text_area = self.wait_for_and_find_element(*self._reject_input_text_locator)
        text_area.send_keys("oh no")

    def submit_rejection(self):
        button = self.wait_for_and_find_element(*self._reject_input_text_submit_locator)
        button.click()

    @property
    def experiment_slug(self):
        return self.wait_for_and_find_element(*self._header_slug, "header slug").text

    @property
    def experiment_status(self):
        el = self.wait_for_and_find_element(*self._experiment_status_icon_locator)
        return el.text

    @property
    def launch_without_preview(self):
        return self.wait_for_and_find_element(*self._launch_without_preview_locator)

    def launch_to_preview(self):
        self.wait_for_and_find_element(*self._launch_to_preview_locator).click()
        return self

    @property
    def request_review(self):
        return self.RequestReview(self)

    def approve(self):
        self.wait_for_and_find_element(*self._approve_request_button_locator).click()

    def request_update_and_approve(self):
        self.request_update()
        self.wait_for_and_find_element(*self._approve_request_button_locator).click()

    def request_update_and_reject(self):
        self.request_update()
        self.wait_for_and_find_element(*self._reject_request_button_locator).click()

    @property
    def request_update_action(self):
        return self.wait_for_and_find_element(*self._update_request_locator)

    def request_update(self):
        self.request_update_action.click()

    def launch_and_approve(self):
        el = self.launch_without_preview
        self.js_click(el)
        self.request_review.click_launch_checkboxes()
        el = self.request_review.request_launch_button
        self.js_click(el)
        self.approve()

    def end_and_approve(self):
        el = self.wait_for_and_find_element(*self._end_experiment_button_locator)
        el.click()
        self.approve()

    @property
    def rejected_text(self):
        el = self.wait_for_and_find_element(*self._rejected_text_alert_locator)
        return el.is_displayed()

    @property
    def timeout_text(self):
        return self.selenium.wait_for_and_find_element(*self._timeout_alert_locator)

    class RequestReview(Region, Base):
        PAGE_TITLE = "Review Region"
        _root_locator = (By.CSS_SELECTOR, "#launch-controls")
        _checkbox1_locator = (By.CSS_SELECTOR, "#checkbox-1")
        _checkbox2_locator = (By.CSS_SELECTOR, "#checkbox-2")
        _request_launch_locator = (By.CSS_SELECTOR, "#request-launch-button")

        def click_launch_checkboxes(self):
            checkbox1 = self.wait_for_and_find_element(*self._checkbox1_locator)
            checkbox2 = self.wait_for_and_find_element(*self._checkbox2_locator)
            self.js_click(checkbox1)
            self.js_click(checkbox2)

        @property
        def request_launch_button(self):
            return self.wait_for_and_find_element(*self._request_launch_locator)

    def archive(self):
        self.wait_for_and_find_element(*self._archive_button_locator).click()

    @property
    def archive_label(self):
        return self.wait_for_and_find_element(*self._archive_label_locator)

    @property
    def clone_action(self):
        return self.wait_for_and_find_element(*self._clone_action_locator)

    @property
    def clone_name_field(self):
        return self.wait_for_and_find_element(*self._clone_name_field_locator)

    @property
    def clone_name(self):
        return self.clone_name_field.text

    @clone_name.setter
    def clone_name(self, text=None):
        # Control-a before typing, in order to fully overwrite default value
        self.clone_name_field.send_keys(f"{Keys.CONTROL}a")
        self.clone_name_field.send_keys(f"{text}")

    @property
    def promote_to_rollout_name(self):
        return self.wait_for_and_find_element(*self._promote_to_rollout_name_locator).text

    @promote_to_rollout_name.setter
    def promote_to_rollout_name(self, text=None):
        el = self.wait_for_and_find_element(*self._promote_to_rollout_name_locator)
        el.send_keys(f"{Keys.CONTROL}a", f"{text}")

    @property
    def promote_to_rollout_save(self):
        return self.wait_for_and_find_element(*self._promote_to_rollout_save_locator)

    @property
    def clone_save(self):
        return self.wait_for_and_find_element(*self._clone_save_locator)

    def clone(self):
        self.clone_action.click()
        self.clone_save.click()

    @property
    def promote_to_rollout_buttons(self):
        return self.wait_for_and_find_elements(*self._promote_rollout_locator)

    def promote_first_branch_to_rollout(self):
        self.promote_to_rollout_buttons[0].click()
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        self.promote_to_rollout_name = f"Rollout {random_chars}"
        self.promote_to_rollout_save.click()

    @property
    def takeaways_edit_button(self):
        return self.wait_for_and_find_element(*self._takeaways_edit_button)

    @property
    def takeaways_save_button(self):
        return self.wait_for_and_find_element(*self._takeaways_save_button)

    def takeaways_recommendation_checkbox_button(self, value=""):
        selection_locator = (
            By.ID,
            f"conclusionRecommendation-{value}",
        )
        return self.wait_for_and_find_element(*selection_locator)

    @property
    def takeaways_recommendation_badge_text(self):
        return self.wait_for_and_find_element(*self._takeaways_recommendation_badge).text

    @property
    def takeaways_summary_field(self):
        return self.wait_for_and_find_element(*self._takeaways_summary_field)

    @takeaways_summary_field.setter
    def takeaways_summary_field(self, text=None):
        # Control-a before typing, in order to fully overwrite default value
        self.takeaways_summary_field.send_keys(f"{Keys.CONTROL}a")
        self.takeaways_summary_field.send_keys(f"{text}")

    @property
    def takeaways_summary_text(self):
        return self.wait_for_and_find_element(*self._takeaways_summary_text).text

    def set_takeaways(self, takeaways, recommendation):
        self.takeaways_edit_button.click()
        self.takeaways_summary_field = takeaways
        self.js_click(self.takeaways_recommendation_checkbox_button(recommendation))
        self.js_click(self.takeaways_save_button)

    @property
    def branch_screenshot_description(self):
        return self.wait_for_and_find_elements(
            *self._branch_screenshot_description_locator, "branch screenshot description"
        )[0].text

    @property
    def branch_screenshot_image(self):
        return self.wait_for_and_find_elements(
            *self._branch_screenshot_image_locator, "branch screenshot image"
        )[0]

    @property
    def audience_table(self):
        return self.wait_for_and_find_element(
            *self._audience_section_locator, "audience table"
        )

    @property
    def first_run(self):
        return self.wait_for_and_find_elements(
            *self._audience_is_first_run_locator, "audience table first run"
        )[0].text

    @property
    def proposed_release_date(self):
        return self.wait_for_and_find_elements(
            *self._audience_proposed_release_date_locator,
            "audience table proposed release date",
        )[0].text

    def wait_for_timeline_visible(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._timeline_locator),
            message="Summary Page: could not find timeline",
        )

    def wait_for_timeline_release_date(self):
        self.wait.until(
            EC.presence_of_all_elements_located(
                self._timeline_proposed_release_date_locator
            ),
            message="Summary Page: could not find release date on timeline",
        )

    def wait_until_timeline_release_date_not_found(self):
        self.wait.until_not(
            EC.presence_of_element_located(self._timeline_proposed_release_date_locator),
            message="Summary Page: found timeline release date",
        )

    def wait_until_audience_release_date_not_found(self):
        self.wait.until_not(
            EC.presence_of_element_located(self._audience_proposed_release_date_locator),
            message="Summary Page: found audience release date",
        )

    def wait_until_audience_first_run_not_found(self):
        self.wait.until_not(
            EC.presence_of_element_located(self._audience_is_first_run_locator),
            message="Summary Page: found audience first run",
        )
