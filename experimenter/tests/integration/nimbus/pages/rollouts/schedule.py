from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from nimbus.pages.rollouts.form_base import FormBase


class ScheduleSection(FormBase):
    """Schedule section of the rollout detail page."""

    PAGE_TITLE = "Rollout Schedule"
    CARD_ID = "schedule"

    _rollout_plan_locator = (By.ID, "id_rollout_plan")
    _add_phase_button_locator = (By.ID, "rollout-schedule-add-phase")
    _advance_observations_locator = (By.ID, "id_rollout_advance_observations")
    _pause_observations_locator = (By.ID, "id_rollout_pause_observations")
    _displayed_phases_locator = (By.ID, "rollout-schedule-phases")
    _displayed_advance_observations_locator = (
        By.ID,
        "rollout-schedule-advance-observations",
    )
    _displayed_pause_observations_locator = (
        By.ID,
        "rollout-schedule-pause-observations",
    )

    def _phase_locator(self, index, field):
        return (By.ID, f"id_rollout_phases-{index}-{field}")

    @property
    def rollout_plan(self):
        return self.get_select(self._rollout_plan_locator).get_attribute("value")

    def apply_rollout_plan(self, plan):
        form = self._wait_present(self._form_locator)
        self.set_select(self._rollout_plan_locator, plan)
        self.wait.until(EC.staleness_of(form))
        self._wait_present(self._form_locator)
        return self

    def add_phase(self):
        form = self._wait_present(self._form_locator)
        self.click_element(self._add_phase_button_locator)
        self.wait.until(EC.staleness_of(form))
        self._wait_present(self._form_locator)
        return self

    def set_phase_population(self, index, value):
        self.set_input(self._phase_locator(index, "population_percent"), value)

    def set_phase_start_date(self, index, value):
        self.set_input(self._phase_locator(index, "start_date"), value)

    def set_phase_end_date(self, index, value):
        self.set_input(self._phase_locator(index, "end_date"), value)

    @property
    def advance_observations(self):
        return self.get_input(self._advance_observations_locator).get_attribute("value")

    @advance_observations.setter
    def advance_observations(self, value):
        self.set_input(self._advance_observations_locator, value)

    @property
    def pause_observations(self):
        return self.get_input(self._pause_observations_locator).get_attribute("value")

    @pause_observations.setter
    def pause_observations(self, value):
        self.set_input(self._pause_observations_locator, value)

    @property
    def displayed_phase_count(self):
        phases = self._wait_present(self._displayed_phases_locator)
        return len(phases.find_elements(By.TAG_NAME, "tr"))

    def displayed_phase_population(self, index):
        locator = (By.ID, f"rollout-schedule-phase-{index}-population")
        return self._wait_present(locator).text

    @property
    def displayed_advance_observations(self):
        return self._wait_present(self._displayed_advance_observations_locator).text

    @property
    def displayed_pause_observations(self):
        return self._wait_present(self._displayed_pause_observations_locator).text
