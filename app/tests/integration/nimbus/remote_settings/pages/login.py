from pypom import Page
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Login(Page):

    _root_locator = (By.CSS_SELECTOR, ".container-fluid")
    _auth_type_checkbox_locator = (
        By.CSS_SELECTOR,
        "div.radio:nth-child(2) label span input",
    )
    _username_locator = (By.CSS_SELECTOR, "#root_credentials_username")
    _password_locator = (By.CSS_SELECTOR, "#root_credentials_password")
    _login_button_locator = (By.CSS_SELECTOR, ".btn-info")

    def wait_for_page_to_load(self):
        self.wait.until(EC.presence_of_element_located(self._root_locator))
        return self

    @property
    def kinto_auth(self):
        return self.find_element(*self._auth_type_checkbox_locator)

    def login(self, user="review", password="review"):
        username = self.find_element(*self._username_locator)
        username.send_keys(user)
        passwrd = self.find_element(*self._password_locator)
        passwrd.send_keys(password)
        self.find_element(*self._login_button_locator).click()

        from nimbus.remote_settings.pages.dashboard import Dashboard

        return Dashboard(self.selenium, self.base_url).wait_for_page_to_load()
