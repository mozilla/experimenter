"""Representaion of the Experiment Detail Page."""

import random
import string

from selenium.webdriver.common.by import By
from pypom import Region

from pages.base import Base

class DetailPage(Base):

    _edit_branches_btn_locator = (By.CSS_SELECTOR,"#branches-edit-btn")

    _page_wait_locator = (
        By.CSS_SELECTOR,
        "body.page-detail-view",
    )

    def click_edit(self):
        self.find_element(*self._edit_branches_btn_locator).click()

        from pages.experiment_design import DesignPage

        return DesignPage(
            self.driver, self.base_url
        ).wait_for_page_to_load()
