from selenium.webdriver.common.by import By

from nimbus.pages.base import Base


class ReviewPage(Base):
    """Experiment Review Page."""
    _page_wait_locator = (By.CSS_SELECTOR, "#PageRequestReview")
