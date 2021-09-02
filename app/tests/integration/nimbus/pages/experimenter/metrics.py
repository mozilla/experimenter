from nimbus.pages.experimenter.audience import AudiencePage
from nimbus.pages.experimenter.base import ExperimenterBase
from selenium.webdriver.common.by import By


class MetricsPage(ExperimenterBase):
    """Experiment Metrics Page.."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageEditMetrics")
    NEXT_PAGE = AudiencePage
