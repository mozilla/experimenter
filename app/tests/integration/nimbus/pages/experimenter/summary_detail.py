import random
import string

from nimbus.pages.experimenter.base import ExperimenterBase
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC


class SummaryDetailPage(ExperimenterBase):
    """Experiment Summary Detail Page."""

    _page_wait_locator = (By.CSS_SELECTOR, "#PageSummaryDetails")
    _promote_rollout_locator = (By.CSS_SELECTOR, 'button[data-testid="promote-rollout"]')
    _clone_name_field_locator = (
        By.CSS_SELECTOR,
        'form[data-testid="FormClone"] input[name="name"]',
    )
    _clone_save_locator = (By.CSS_SELECTOR, ".modal .btn-primary")
    _clone_parent_locator = (By.CSS_SELECTOR, 'p[data-testid="header-experiment-parent"]')
    PAGE_TITLE = "Summary Detail Page"

    @property
    def clone_name_field(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._clone_name_field_locator),
            message="Summary Page: could not find clone name field",
        )
        return self.find_element(*self._clone_name_field_locator)

    @property
    def clone_name(self):
        return self.clone_name_field.text

    @clone_name.setter
    def clone_name(self, text=None):
        # Control-a before typing, in order to fully overwrite default value
        self.clone_name_field.send_keys(Keys.CONTROL + "a")
        self.clone_name_field.send_keys(f"{text}")

    @property
    def clone_save(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._clone_save_locator),
            message="Summary Page: could not find clone save",
        )
        return self.find_element(*self._clone_save_locator)

    @property
    def promote_to_rollout_buttons(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._promote_rollout_locator),
            message="Summary Page: could not find promote to rollout buttons",
        )
        return self.find_elements(*self._promote_rollout_locator)

    def promote_first_branch_to_rollout(self):
        self.promote_to_rollout_buttons[0].click()
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        self.clone_name = f"Rollout {random_chars}"
        self.clone_save.click()

    def wait_for_clone_parent_link_visible(self):
        self.wait.until(
            EC.presence_of_all_elements_located(self._clone_parent_locator),
            message="Summary Page: could not find clone parent",
        )

    def _branch_screenshot(self, slug, screenshot_idx, child):
        return self.wait_for_and_find_elements(
            (
                By.CSS_SELECTOR,
                f'table#{slug} figure[data-testid="branch-screenshot"] {child}',
            ),
            f"branch screenshot {child}",
        )[screenshot_idx]

    def branch_screenshot_description_text(
        self, branch_slug="controlname-1", screenshot_idx=0
    ):
        return self._branch_screenshot(branch_slug, screenshot_idx, "figcaption").text

    def branch_screenshot_image(self, branch_slug="controlname-1", screenshot_idx=0):
        return self._branch_screenshot(branch_slug, screenshot_idx, "img")
