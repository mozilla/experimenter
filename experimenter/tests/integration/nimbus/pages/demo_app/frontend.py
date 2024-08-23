import time

from selenium.webdriver.common.by import By

from nimbus.pages.base import Base


class DemoAppPage(Base):
    PAGE_TITLE = "Demo app frontend"

    def wait_for_result_text(self, text_list):
        xpath_conditions = " | ".join([f".='{text}'" for text in text_list])
        xpath = f"//h1[{' or '.join(xpath_conditions.split(' | '))}]"

        return self.wait_for_and_find_element(By.XPATH, xpath, description=None)

    def fill_and_send_form_data(self, client_id, context, nimbus_preview=False):
        client_xpath = "//input[@placeholder='Client ID']"
        client_id_input = self.wait_for_and_find_element(
            By.XPATH, client_xpath, description=None
        )
        context_xpath = "//input[@placeholder='Context']"
        context_input = self.wait_for_and_find_element(
            By.XPATH, context_xpath, description=None
        )
        time.sleep(2)
        client_id_input.send_keys(client_id)
        context_input.send_keys(context)

        if nimbus_preview:
            preview_checkbox_xpath = "//input[@type='checkbox']"
            preview_checkbox = self.wait_for_and_find_element(
                By.XPATH, preview_checkbox_xpath, description=None
            )
            if not preview_checkbox.is_selected():
                preview_checkbox.click()

    def click_send_my_details(self):
        details_xpath = "//button[contains(text(), 'Send My Details')]"
        send_details_button = self.wait_for_and_find_element(
            By.XPATH, details_xpath, description=None
        )
        send_details_button.click()
