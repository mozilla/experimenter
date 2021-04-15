from nimbus.pages.base import Base
from selenium.webdriver.common.by import By


class ReviewPage(Base):
    """Experiment Review Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageRequestReview")
