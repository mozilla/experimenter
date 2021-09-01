from nimbus.pages.remote_settings.base import RemoteSettingsBase
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Login(RemoteSettingsBase):
    """Remote Settings Login page."""

    _auth_type_checkbox_locator = (By.CSS_SELECTOR, 'input[value="accounts"]')
    _username_locator = (By.CSS_SELECTOR, "#root_credentials_username")
    _password_locator = (By.CSS_SELECTOR, "#root_credentials_password")
    _login_button_locator = (By.CSS_SELECTOR, 'button[type="submit"]')
    _logged_in_locator = (By.CSS_SELECTOR, ".session-info-bar")

    def wait_for_page_to_load(self):
        self.wait.until(
            EC.presence_of_element_located(self._page_wait_locator),
            message="Kinto Login: Page wait locator not found",
        )
        return self

    def wait_for_login(self):
        self.wait.until(
            EC.presence_of_element_located(self._logged_in_locator),
            message="Kinto Login: Unable to verify logged in status",
        )

    @property
    def kinto_account_type(self):
        self.wait.until(
            EC.presence_of_element_located(self._auth_type_checkbox_locator),
            message="Kinto Login: Unable to find account type input",
        )
        return self.find_element(*self._auth_type_checkbox_locator)

    @property
    def username(self):
        self.wait.until(
            EC.presence_of_element_located(self._username_locator),
            message="Kinto Login: Unable to find username input",
        )
        return self.find_element(*self._username_locator)

    @property
    def password(self):
        self.wait.until(
            EC.presence_of_element_located(self._password_locator),
            message="Kinto Login: Unable to find password input",
        )
        return self.find_element(*self._password_locator)

    @property
    def login_button(self):
        self.wait.until(
            EC.presence_of_element_located(self._login_button_locator),
            message="Kinto Login: Unable to find login button",
        )
        return self.find_element(*self._login_button_locator)

    def login(self, user="review", password="review"):
        self.kinto_account_type.click()
        self.username.send_keys(user)
        self.password.send_keys(password)
        self.login_button.click()
        self.wait_for_login()
