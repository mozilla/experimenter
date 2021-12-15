from nimbus.pages.experimenter.base import ExperimenterBase
from pypom import Region
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC


class SummaryPage(ExperimenterBase):
    """Experiment Summary Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageSummary")
    _header_slug = (By.CSS_SELECTOR, 'p[data-testid="header-experiment-slug"]')
    _approve_request_button_locator = (By.CSS_SELECTOR, "#approve-request-button")
    _launch_to_preview_locator = (By.CSS_SELECTOR, "#launch-to-preview-button")
    _launch_without_preview_locator = (By.CSS_SELECTOR, "#launch-to-review-button")
    _rejected_text_alert_locator = (By.CSS_SELECTOR, '[data-testid="rejection-notice"]')
    _timeout_alert_locator = (By.CSS_SELECTOR, '[data-testid="timeout-notice"]')
    _status_live_locator = (By.CSS_SELECTOR, ".status-Live.border-primary")
    _status_preview_locator = (By.CSS_SELECTOR, ".status-Preview.border-primary")
    _status_complete_locator = (By.CSS_SELECTOR, ".status-Complete.border-primary")
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
    _clone_action_locator = (By.CSS_SELECTOR, 'button[data-testid="action-clone"]')
    _clone_name_field_locator = (
        By.CSS_SELECTOR,
        'form[data-testid="FormClone"] input[name="name"]',
    )
    _clone_save_locator = (By.CSS_SELECTOR, ".modal .btn-primary")
    _clone_parent_locator = (By.CSS_SELECTOR, 'p[data-testid="header-experiment-parent"]')
    _takeaways_edit_button = (By.CSS_SELECTOR, 'button[data-testid="edit-takeaways"]')
    _takeaways_save_button = (
        By.CSS_SELECTOR,
        'button[data-testid="takeaways-edit-save"]',
    )
    _takeaways_recommendation_field = (
        By.CSS_SELECTOR,
        'form[data-testid="FormTakeaways"] input[name="conclusionRecommendation"]',
    )
    _takeaways_summary_field = (
        By.CSS_SELECTOR,
        'form[data-testid="FormTakeaways"] textarea[name="takeawaysSummary"]',
    )
    _takeaways_summary_text = (
        By.CSS_SELECTOR,
        'div[data-testid="takeaways-summary-rendered"]',
    )
    _takeaways_recommendation_badge = (
        By.CSS_SELECTOR,
        'span[data-testid="conclusion-recommendation-status"]',
    )

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

    def wait_for_live_status(self):
        self.wait_with_refresh(
            self._status_live_locator, "Summary Page: Unable to find live status"
        )

    def wait_for_preview_status(self):
        self.wait_with_refresh(
            self._status_preview_locator, "Summary Page: Unable to find preview status"
        )

    def wait_for_complete_status(self):
        self.wait_with_refresh(
            self._status_complete_locator, "Summary Page: Unable to find complete status"
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

    @property
    def experiment_slug(self):
        return self.wait_for_and_find_element(self._header_slug, "header slug").text

    @property
    def experiment_status(self):
        el = self.find_element(*self._experiment_status_icon_locator)
        return el.text

    @property
    def launch_without_preview(self):
        return self.find_element(*self._launch_without_preview_locator)

    def launch_to_preview(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._launch_to_preview_locator),
            message="Summary Page: could not find preview button",
        )
        self.find_element(*self._launch_to_preview_locator).click()
        return self

    @property
    def request_review(self):
        return self.RequestReview(self)

    def approve(self):
        self.wait.until(
            EC.presence_of_element_located(self._approve_request_button_locator)
        )
        self.find_element(*self._approve_request_button_locator).click()

    def launch_and_approve(self):
        self.launch_without_preview.click()
        self.request_review.click_launch_checkboxes()
        self.request_review.request_launch_button.click()
        self.approve()

    def end_and_approve(self, action="End"):
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
        self.approve()

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

    def archive(self):
        self.find_element(*self._archive_button_locator).click()

    @property
    def archive_label(self):
        return self.find_element(*self._archive_label_locator)

    @property
    def clone_action(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._clone_action_locator),
            message="Summary Page: could not find clone action",
        )
        return self.find_element(*self._clone_action_locator)

    @property
    def clone_name_field(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._clone_name_field_locator),
            message="Summary Page: could not find clone name field",
        )
        return self.find_element(*self._clone_name_field_locator)

    @property
    def clone_name(self):
        return self.clone_name_field.text

    @clone_name.setter
    def clone_name(self, text=None):
        # Control-a before typing, in order to fully overwrite default value
        self.clone_name_field.send_keys(Keys.CONTROL + "a")
        self.clone_name_field.send_keys(f"{text}")

    @property
    def clone_save(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._clone_save_locator),
            message="Summary Page: could not find clone save",
        )
        return self.find_element(*self._clone_save_locator)

    def clone(self):
        self.clone_action.click()
        self.clone_save.click()

    @property
    def takeaways_edit_button(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._takeaways_edit_button),
            message="Summary Page: could not find takeaways edit button",
        )
        return self.find_element(*self._takeaways_edit_button)

    @property
    def takeaways_save_button(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._takeaways_save_button),
            message="Summary Page: could not find takeaways save button",
        )
        return self.find_element(*self._takeaways_save_button)

    def takeaways_recommendation_radio_button(self, value=""):
        selection_locator = (
            By.CSS_SELECTOR,
            f'input[type=radio][name="conclusionRecommendation"][value="{value}"]',
        )
        self.wait.until(
            EC.presence_of_all_elements_located(selection_locator),
            message=(
                f"Summary Page: could not find recommendation radio button "
                f"for {value}"
            ),
        )
        return self.find_element(*selection_locator)

    @property
    def takeaways_recommendation_badge_text(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._takeaways_recommendation_badge),
            message="Summary Page: could not find takeaways recommendation badge",
        )
        return self.find_element(*self._takeaways_recommendation_badge).text

    @property
    def takeaways_summary_field(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._takeaways_summary_field),
            message="Summary Page: could not find takeaways summary field",
        )
        return self.find_element(*self._takeaways_summary_field)

    @takeaways_summary_field.setter
    def takeaways_summary_field(self, text=None):
        # Control-a before typing, in order to fully overwrite default value
        self.takeaways_summary_field.send_keys(Keys.CONTROL + "a")
        self.takeaways_summary_field.send_keys(f"{text}")

    @property
    def takeaways_summary_text(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._takeaways_summary_text),
            message="Summary Page: could not find takeaways summary text",
        )
        return self.find_element(*self._takeaways_summary_text).text
