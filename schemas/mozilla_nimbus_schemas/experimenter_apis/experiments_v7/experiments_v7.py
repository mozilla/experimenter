from pydantic import Field

from mozilla_nimbus_schemas.experimenter_apis.common import (
    BaseExperimentBranch,
    ExperimentLocalizations,
    _CommonBaseExperiment,
)


class NimbusExperimentV7(_CommonBaseExperiment):
    """A Nimbus experiment for V7."""

    localizations: ExperimentLocalizations | None = Field(
        description="Per-locale localization substitutions.", default=None
    )

    branches: list[BaseExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )
