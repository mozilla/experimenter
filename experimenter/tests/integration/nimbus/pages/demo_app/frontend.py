import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from nimbus.pages.base import Base


class DemoAppPage(Base):
    def __init__(self, driver):
        self.driver = driver

    def navigate_to(self):
        demo_app_url = "http://demo-app-frontend:3000/"
        self.driver.get(demo_app_url)

    def wait_for_result_text(self, text_list):
        xpath_conditions = " | ".join([f".='{text}'" for text in text_list])
        xpath = f"//h1[{' or '.join([''] + xpath_conditions.split(' | '))}]"

        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

    def fill_and_send_form_data(self, client_id, context):
        time.sleep(10)
        client_id_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Client ID']")
            )
        )
        context_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Context']")
            )
        )

        client_id_input.send_keys(client_id)
        context_input.send_keys(context)

    def click_send_my_details(self):
        send_details_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Send My Details')]")
            )
        )
        assert send_details_button.is_displayed() and send_details_button.is_enabled()
        send_details_button.click()
