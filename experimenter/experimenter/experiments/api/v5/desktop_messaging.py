from typing import Any

from pydantic import BaseModel, ConfigDict

from experimenter.experiments.constants import NimbusConstants


class DesktopMessageAction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str | None = None
    data: "DesktopMessageActionData | None" = None

    def action_types(self) -> set[str]:
        action_types = set()
        if self.type:
            action_types.add(self.type)
        if self.data and self.data.actions:
            for nested_action in self.data.actions:
                action_types |= nested_action.action_types()
        return action_types


class DesktopMessageActionData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    actions: list[DesktopMessageAction] | None = None


DesktopMessageAction.model_rebuild()


class DesktopMessageButton(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: DesktopMessageAction | None = None


class DesktopMessageCfrButtons(BaseModel):
    model_config = ConfigDict(extra="ignore")

    primary: DesktopMessageButton | None = None
    secondary: list[DesktopMessageButton] | None = None


class DesktopMessageScreenContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    primary_button: DesktopMessageButton | None = None
    secondary_button: DesktopMessageButton | None = None
    additional_button: DesktopMessageButton | None = None


class DesktopMessageScreen(BaseModel):
    model_config = ConfigDict(extra="ignore")

    content: DesktopMessageScreenContent | None = None


class DesktopMessageContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    screens: list[DesktopMessageScreen] | None = None
    primary_button: DesktopMessageButton | None = None
    additional_button: DesktopMessageButton | None = None
    buttons: list[DesktopMessageButton] | DesktopMessageCfrButtons | None = None


class DesktopMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    template: str | None = None
    targeting: str | None = None
    trigger: Any = None
    groups: list[str] | None = None
    content: DesktopMessageContent | None = None

    @property
    def trigger_id(self) -> str | None:
        if isinstance(self.trigger, dict) and isinstance(self.trigger.get("id"), str):
            return self.trigger["id"]
        return None

    def action_types(self) -> set[str]:
        action_types = set()
        if self.content is None:
            return action_types

        buttons = (
            self.content.primary_button,
            self.content.additional_button,
        )
        for screen in self.content.screens or []:
            if screen.content:
                buttons += (
                    screen.content.primary_button,
                    screen.content.secondary_button,
                    screen.content.additional_button,
                )
        for button in buttons:
            if button and button.action:
                action_types |= button.action.action_types()

        content_buttons = self.content.buttons
        if isinstance(content_buttons, list):
            for button in content_buttons:
                if button.action:
                    action_types |= button.action.action_types()
        elif isinstance(content_buttons, DesktopMessageCfrButtons):
            if content_buttons.primary and content_buttons.primary.action:
                action_types |= content_buttons.primary.action.action_types()
            for button in content_buttons.secondary or []:
                if button.action:
                    action_types |= button.action.action_types()

        return action_types

    def required_groups(self) -> set[str]:
        required_groups = set(
            NimbusConstants.DESKTOP_MESSAGING_REQUIRED_GROUPS_BY_TEMPLATE.get(
                self.template, ()
            )
        )

        if self.targeting:
            for (
                substring,
                groups,
            ) in NimbusConstants.DESKTOP_MESSAGING_REQUIRED_GROUPS_BY_TARGETING.items():
                if substring in self.targeting:
                    required_groups.update(groups)

        required_groups.update(
            NimbusConstants.DESKTOP_MESSAGING_REQUIRED_GROUPS_BY_TRIGGER.get(
                self.trigger_id, ()
            )
        )

        for action_type in self.action_types():
            required_groups.update(
                NimbusConstants.DESKTOP_MESSAGING_REQUIRED_GROUPS_BY_ACTION_TYPE.get(
                    action_type, ()
                )
            )

        return required_groups

    def has_frequency_group_or_preference_check(self) -> bool:
        if self.groups:
            return True

        if self.targeting is None:
            return False

        return any(
            preference_check in self.targeting
            for preference_check in (
                NimbusConstants.DESKTOP_MESSAGING_FREQUENCY_GROUP_PREFERENCE_CHECKS
            )
        )


class DesktopMultiMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    template: str | None = None
    messages: list[DesktopMessage] | None = None
