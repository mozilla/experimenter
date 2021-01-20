import graphene

from experimenter.experiments.api.v5.types import (
    NimbusExperimentApplication,
    NimbusExperimentChannel,
    NimbusExperimentDocumentationLink,
    NimbusExperimentFirefoxMinVersion,
    NimbusExperimentStatus,
    NimbusExperimentTargetingConfigSlug,
)


class BranchType(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    ratio = graphene.Int(required=True)
    feature_enabled = graphene.Boolean()
    feature_value = graphene.String()


class DocumentationLinkType(graphene.InputObjectType):
    title = NimbusExperimentDocumentationLink(required=True)
    link = graphene.String(required=True)


class ReferenceBranchType(BranchType):
    class Meta:
        description = "The control branch"


class TreatmentBranchType(BranchType):
    class Meta:
        description = (
            "The treatment branch that should be in this position on the experiment."
        )


class ExperimentInput(graphene.InputObjectType):
    client_mutation_id = graphene.String()
    id = graphene.Int()
    status = NimbusExperimentStatus()
    name = graphene.String()
    hypothesis = graphene.String()
    application = NimbusExperimentApplication()
    public_description = graphene.String()
    risk_mitigation_link = graphene.String()
    feature_config_id = graphene.Int()
    documentation_links = graphene.List(DocumentationLinkType)
    reference_branch = graphene.Field(ReferenceBranchType)
    treatment_branches = graphene.List(TreatmentBranchType)
    primary_probe_set_ids = graphene.List(graphene.Int)
    secondary_probe_set_ids = graphene.List(graphene.Int)
    channel = NimbusExperimentChannel()
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    population_percent = graphene.String()
    proposed_duration = graphene.Int()
    proposed_enrollment = graphene.String()
    targeting_config_slug = NimbusExperimentTargetingConfigSlug()
    total_enrolled_clients = graphene.Int()
