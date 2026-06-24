from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

from mozilla_nimbus_schemas.experimenter_apis.common import (
    BaseExperiment,
    BaseExperimentBranch,
)


class ExperimentBranchV7(BaseExperimentBranch):
    description: str = Field(description="A description of the branch.")
    screenshots: list[str] = Field(
        description="The URLs of any screenshots associated with the branch.",
    )


class DocumentationLink(BaseModel):
    title: str = Field(description="The name associated with the link.")
    link: str = Field(description="The URL associated with the link.")


class NimbusExperimentV7(BaseExperiment):
    """A Nimbus experiment for V7."""

    channels: list[str] | SkipJsonSchema[None] = Field(
        description=(
            "The channels available for the experiment.\n"
            "This field should be preferred over the channel field."
        ),
        default=None,
    )

    branches: list[ExperimentBranchV7] = Field(
        description="Branch configuration for the experiment.",
    )

    documentationLinks: list[DocumentationLink] = Field(
        description="All documentation links associated with this experiment.",
    )
