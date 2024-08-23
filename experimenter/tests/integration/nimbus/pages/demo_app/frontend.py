import time

from selenium.webdriver.common.by import By

from nimbus.pages.base import Base


class DemoAppPage(Base):
    PAGE_TITLE = "Demo app frontend"
    CONTROL_BRANCH = "Control branch"
    TREATMENT_BRANCH = "Treatment branch"

    # XPaths for elements
    CLIENT_ID_INPUT_XPATH = "//input[@placeholder='Client ID']"
    CONTEXT_INPUT_XPATH = "//input[@placeholder='Context']"
    PREVIEW_CHECKBOX_XPATH = "//input[@type='checkbox']"
    SEND_DETAILS_BUTTON_XPATH = "//button[contains(text(), 'Send My Details')]"
    RESULT_TEXT_XPATH_TEMPLATE = "//h1[{}]"

    # Client dictionaries
    CLIENT_1 = {"client_id": "dummy_client_id", "context": '{"test1":"test2"}'}

    CLIENT_2 = {"client_id": "example1", "context": '{"test1":"test2"}'}

    CLIENT_3 = {"client_id": "test", "context": '{"language":"en", "region":"CA"}'}

    # Branch value constants
    REFERENCE_BRANCH_VALUE = f'{{"enabled": true, "something": "{CONTROL_BRANCH}"}}'
    TREATMENT_BRANCH_VALUE = f'{{"enabled": true, "something": "{TREATMENT_BRANCH}"}}'

    # Default values
    DEFAULT_NOT_ENROLLED_TEXT = "Not Enrolled"
    DEFAULT_WICKED_TEXT = "wicked"

    def wait_for_result_text(self, text_list):
        """Wait for and return the result text element matching any text in text_list."""
        xpath_conditions = " or ".join([f".='{text}'" for text in text_list])
        xpath = self.RESULT_TEXT_XPATH_TEMPLATE.format(xpath_conditions)
        return self.wait_for_and_find_element(By.XPATH, xpath, description="Result Text")

    def fill_form(self, client_id, context):
        """Fill the form with client_id and context."""
        self.enter_text(self.CLIENT_ID_INPUT_XPATH, client_id, "Client ID Input")
        self.enter_text(self.CONTEXT_INPUT_XPATH, context, "Context Input")

    def enable_nimbus_preview(self):
        """Enable Nimbus Preview checkbox if not already selected."""
        preview_checkbox = self.wait_for_and_find_element(
            By.XPATH, self.PREVIEW_CHECKBOX_XPATH, description="Nimbus Preview Checkbox"
        )
        if not preview_checkbox.is_selected():
            preview_checkbox.click()

    def click_send_my_details(self):
        """Click the 'Send My Details' button."""
        self.click_button(self.SEND_DETAILS_BUTTON_XPATH, "Send My Details Button")

    def fill_and_send_form_data(self, client_id, context, nimbus_preview=False):
        """Fill the form with client_id and context, optionally enable Nimbus preview, and submit the form."""
        self.fill_form(client_id, context)
        if nimbus_preview:
            self.enable_nimbus_preview()
        time.sleep(10)  # Adjust as needed based on test environment
        self.click_send_my_details()

    def enter_text(self, xpath, text, description):
        """Helper method to enter text into an input field."""
        input_element = self.wait_for_and_find_element(
            By.XPATH, xpath, description=description
        )
        input_element.clear()
        input_element.send_keys(text)

    def click_button(self, xpath, description):
        """Helper method to click a button."""
        button_element = self.wait_for_and_find_element(
            By.XPATH, xpath, description=description
        )
        button_element.click()
