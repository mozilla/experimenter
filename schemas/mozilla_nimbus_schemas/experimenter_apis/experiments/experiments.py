from copy import deepcopy
from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import Self

from mozilla_nimbus_schemas.experimenter_apis.common import (
    BaseExperiment,
    BaseExperimentBranch,
    ExperimentFeatureConfig,
    ExperimentLocalizations,
)


class DesktopPre95FeatureConfig(ExperimentFeatureConfig):
    featureId: Literal["this-is-included-for-desktop-pre-95-support"]
    enabled: Literal[False]
    value: dict[str, Any]


class DesktopExperimentBranch(BaseExperimentBranch):
    """The branch definition supported on Firefox Desktop 95+."""

    # Firefox Desktop-specific fields should be added to *this* schema. They will be
    # inherited by the stricter DesktopAllVersionsExperimentBranch schema.

    firefoxLabsTitle: str | None = Field(
        description="The branch title shown in Firefox Labs (Fluent ID)", default=None
    )


class SdkExperimentBranch(BaseExperimentBranch):
    """The branch definition for SDK-based applications.

    Supported on Firefox for Android 96+, Firefox for iOS 39+, and all versions of Cirrus.
    """


class DesktopAllVersionsExperimentBranch(DesktopExperimentBranch):
    """The branch definition supported on all Firefox Desktop versions.

    This version requires the feature field to be present to support older Firefox Desktop
    clients.
    """

    # Firefox Desktop-specific fields should be added to DesktopExperimentBranch. They
    # will be inherited by this schema.

    feature: DesktopPre95FeatureConfig = Field(
        description=(
            "The feature key must be provided with values to prevent crashes if the "
            "experiment is encountered by Desktop clients earlier than version 95."
        )
    )


def desktop_nimbus_experiment_json_schema_extras():
    extras = deepcopy(BaseExperiment.model_config["json_schema_extra"])

    firefox_labs_schema = extras["dependentSchemas"]["isFirefoxLabsOptIn"]
    firefox_labs_schema["then"].update(
        {
            # On Desktop, firefoxLabsGroup is also required.
            "required": sorted(
                [
                    *firefox_labs_schema["then"]["required"],
                    "firefoxLabsGroup",
                ]
            ),
            # Additionally, Desktop validates multi-branch Firefox Labs opt-ins.
            "if": {
                "properties": {
                    "isRollout": {"const": False},
                },
                "required": ["isRollout"],
            },
            "then": {
                "properties": {
                    "branches": {
                        "items": {
                            "required": ["firefoxLabsTitle"],
                        },
                    },
                },
            },
        }
    )

    return extras


class DesktopNimbusExperiment(BaseExperiment):
    """A Nimbus experiment for Firefox Desktop.

    This schema is less strict than DesktopAllVersionsNimbusExperiment and is intended for
    use in Firefox Desktop.
    """

    # Firefox Desktop-specific fields should be added to *this* schema. They will be
    # inherited by the stricter DesktopAllVersionsNimbusExperiment schema.

    branches: list[DesktopExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )

    featureValidationOptOut: bool | SkipJsonSchema[None] = Field(
        description="Opt out of feature schema validation.",
        default=None,
    )

    localizations: ExperimentLocalizations | None = Field(default=None)

    # Only Desktop labs supports groups.
    firefoxLabsGroup: str | None = Field(
        description="The group this should appear under in Firefox Labs",
        default=None,
    )

    @model_validator(mode="after")
    @classmethod
    def validate_firefox_labs_desktop(cls, data: Self) -> Self:
        if data.isFirefoxLabsOptIn:
            if data.firefoxLabsGroup is None:
                raise ValueError(
                    "missing field firefoxLabsGroup (required because isFirefoxLabsOptIn "
                    "is True)"
                )

            if not data.isRollout:
                for branch in data.branches:
                    if branch.firefoxLabsTitle is None:
                        raise ValueError(
                            f"branch with slug {branch.slug} is missing "
                            "firefoxLabsTitle field "
                            "(required because firefoxLabsTitle is True)"
                        )

        return data

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra=desktop_nimbus_experiment_json_schema_extras(),
    )


class DesktopAllVersionsNimbusExperiment(DesktopNimbusExperiment):
    """A Nimbus experiment for Firefox Desktop.

    This schema is more strict than DesktopNimbusExperiment and is backwards
    comaptible with Firefox Desktop versions less than 95. It is intended for use inside
    Experimenter itself.
    """

    # Firefox Desktop-specific fields should be added to DesktopNimbusExperiment. They
    # will be inherited by this schema.

    branches: list[DesktopAllVersionsExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )


def sdk_nimbus_experiment_json_schema_extras():
    extras = deepcopy(BaseExperiment.model_config["json_schema_extra"])

    firefox_labs_schema = extras["dependentSchemas"]["isFirefoxLabsOptIn"]
    firefox_labs_schema["then"].update(
        {
            # For the SDK, isRollout is also required and must be true
            "required": sorted(
                [
                    *firefox_labs_schema["then"]["required"],
                    "isRollout",
                ]
            ),
            "type": "object",
            "properties": {"isRollout": {"const": True}},
        }
    )

    return extras


class SdkNimbusExperiment(BaseExperiment):
    """A Nimbus experiment for Nimbus SDK-based applications."""

    branches: list[SdkExperimentBranch] = Field(
        description="Branch configuration for the SDK experiment."
    )

    @model_validator(mode="after")
    @classmethod
    def validate_firefox_labs_desktop(cls, data: Self) -> Self:
        if data.isFirefoxLabsOptIn and not data.isRollout:
            raise ValueError("isFirefoxLabsOptIn requires isRollout")

        return data

    model_config = ConfigDict(
        use_enum_values=True, json_schema_extra=sdk_nimbus_experiment_json_schema_extras()
    )
