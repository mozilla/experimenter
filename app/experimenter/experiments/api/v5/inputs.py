import graphene
from graphene_file_upload.scalars import Upload

from experimenter.experiments.api.v5.types import (
    NimbusExperimentApplication,
    NimbusExperimentChannel,
    NimbusExperimentConclusionRecommendation,
    NimbusExperimentDocumentationLink,
    NimbusExperimentFirefoxMinVersion,
    NimbusExperimentPublishStatus,
    NimbusExperimentStatus,
)


class BranchScreenshotType(graphene.InputObjectType):
    image = Upload(required=True)
    description = graphene.String(required=True)


class BranchType(graphene.InputObjectType):
    id = graphene.Int()
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    ratio = graphene.Int(required=True)
    feature_enabled = graphene.Boolean()
    feature_value = graphene.String()
    screenshots = graphene.List(BranchScreenshotType)


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
    id = graphene.Int()
    is_archived = graphene.Boolean()
    status = NimbusExperimentStatus()
    status_next = NimbusExperimentStatus()
    publish_status = NimbusExperimentPublishStatus()
    name = graphene.String()
    hypothesis = graphene.String()
    application = NimbusExperimentApplication()
    public_description = graphene.String()
    is_enrollment_paused = graphene.Boolean()
    risk_mitigation_link = graphene.String()
    feature_config_id = graphene.Int()
    documentation_links = graphene.List(DocumentationLinkType)
    reference_branch = graphene.Field(ReferenceBranchType)
    treatment_branches = graphene.List(TreatmentBranchType)
    primary_outcomes = graphene.List(graphene.String)
    secondary_outcomes = graphene.List(graphene.String)
    channel = NimbusExperimentChannel()
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    population_percent = graphene.String()
    proposed_duration = graphene.Int()
    proposed_enrollment = graphene.String()
    targeting_config_slug = graphene.String()
    total_enrolled_clients = graphene.Int()
    changelog_message = graphene.String()
    risk_partner_related = graphene.Boolean()
    risk_revenue = graphene.Boolean()
    risk_brand = graphene.Boolean()
    countries = graphene.List(graphene.Int)
    locales = graphene.List(graphene.Int)
    conclusion_recommendation = NimbusExperimentConclusionRecommendation()
    takeaways_summary = graphene.String()


class ExperimentCloneInput(graphene.InputObjectType):
    parent_slug = graphene.String(required=True)
    name = graphene.String(required=True)
    rollout_branch_slug = graphene.String()
