from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from nimbus.pages.rollouts.base import RolloutBase


class FormBase(RolloutBase):
    """Base for editable form sections on the rollout detail page."""

    CARD_ID = None

    def set_select(self, locator, value):
        el = self._wait_present(locator)
        self.selenium.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(
                new Event('change', {bubbles: true})
            );
            """,
            el,
            value,
        )

    def set_select_by_text(self, locator, text):
        el = self._wait_present(locator)
        option = next(option for option in Select(el).options if option.text == text)
        self.set_select(locator, option.get_attribute("value"))

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
        return (By.ID, f"rollout-{self.CARD_ID}-save")

    @property
    def _cancel_button_locator(self):
        return (
            By.CSS_SELECTOR,
            f'#rollout-card-{self.CARD_ID} button[data-card-action="cancel"]',
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
