from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.rollouts.base import RolloutBase


class FormBase(RolloutBase):
    """Base for editable form sections on the rollout detail page."""

    CARD_ID = None

    @property
    def _edit_button_locator(self):
        return (
            By.CSS_SELECTOR,
            f'#rollout-card-{self.CARD_ID} button[aria-label="Edit {self.CARD_ID}"]',
        )

    @property
    def _form_locator(self):
        return (By.CSS_SELECTOR, f"#rollout-{self.CARD_ID}-body form")

    @property
    def _save_button_locator(self):
        return (
            By.CSS_SELECTOR,
            f'#rollout-{self.CARD_ID}-body form button[type="submit"]',
        )

    @property
    def _cancel_button_locator(self):
        return (
            By.CSS_SELECTOR,
            (
                f"#rollout-{self.CARD_ID}-body form "
                f'button[hx-target="#rollout-card-{self.CARD_ID}"]'
            ),
        )

    def edit(self):
        self.click_element(self._edit_button_locator)
        self._wait_present(self._form_locator)
        return self

    def save(self):
        form = self._wait_present(self._form_locator)
        self.click_element(self._save_button_locator)
        self.wait.until(EC.staleness_of(form))
        return self

    def cancel(self):
        self.click_element(self._cancel_button_locator)
        return self
