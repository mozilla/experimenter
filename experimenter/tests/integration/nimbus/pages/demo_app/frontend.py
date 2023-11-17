import time

from nimbus.pages.base import Base


class DemoAppPage(Base):
    def __init__(self, selenium, base_url, **kwargs):
        super().__init__(selenium, base_url, **kwargs)

    def wait_for_result_text(self, text_list):
        xpath_conditions = " | ".join([f".='{text}'" for text in text_list])
        xpath = f"//h1[{' or '.join(xpath_conditions.split(' | '))}]"

        return self.wait_for_and_find_element(self, xpath, description=None)

    def fill_and_send_form_data(self, client_id, context):
        time.sleep(10)
        client_id_input = self.wait_for_and_find_element(
            self, "//input[@placeholder='Client ID']", description=None
        )
        context_input = self.wait_for_and_find_element(
            self, "//input[@placeholder='Context']", description=None
        )

        client_id_input.send_keys(client_id)
        context_input.send_keys(context)

    def click_send_my_details(self):
        send_details_button = self.wait_for_and_find_element(
            self, "//button[contains(text(), 'Send My Details')]", description=None
        )

        send_details_button.click()
