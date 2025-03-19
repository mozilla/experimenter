from pydantic import BaseModel, Field

from mozilla_nimbus_schemas.experimenter_apis.common import (
    BaseExperiment,
    BaseExperimentBranch,
)


class DocumentationLink(BaseModel):
    title: str = Field(description="The name associated with the link.")
    link: str = Field(description="The URL associated with the link.")


class NimbusExperimentV7(BaseExperiment):
    """A Nimbus experiment for V7."""

    branches: list[BaseExperimentBranch] = Field(
        description="Branch configuration for the experiment."
    )

    documentationLinks: list[DocumentationLink] = Field(
        description="All documentation links associated with this experiment."
    )
