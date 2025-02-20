from pydantic import Field

from mozilla_nimbus_schemas.experimenter_apis.common import (
    ExperimentLocalizations,
    _CommonBaseExperiment,
    _CommonBaseExperimentBranch,
)


class NimbusExperimentV7(_CommonBaseExperiment):
    """A Nimbus experiment for V7."""

    localizations: ExperimentLocalizations | None = Field(
        description="Per-locale localization substitutions.", default=None
    )

    branches: list[_CommonBaseExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )
