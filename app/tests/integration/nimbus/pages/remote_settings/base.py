from nimbus.pages.base import Base
from selenium.webdriver.common.by import By


class RemoteSettingsBase(Base):
    """Remote Settings Review Base page."""

    _page_wait_locator = (By.CSS_SELECTOR, ".main")
