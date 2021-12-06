import graphene
from graphene_file_upload.scalars import Upload

from experimenter.experiments.api.v5.types import (
    NimbusExperimentApplicationEnum,
    NimbusExperimentChannelEnum,
    NimbusExperimentConclusionRecommendationEnum,
    NimbusExperimentDocumentationLinkEnum,
    NimbusExperimentFirefoxVersionEnum,
    NimbusExperimentPublishStatusEnum,
    NimbusExperimentStatusEnum,
)


class BranchScreenshotInput(graphene.InputObjectType):
    id = graphene.Int()
    image = Upload()
    description = graphene.String()


class BranchFeatureValueInput(graphene.InputObjectType):
    feature_config = graphene.Int()
    enabled = graphene.Boolean()
    value = graphene.String()


class BranchInput(graphene.InputObjectType):
    id = graphene.Int()
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    ratio = graphene.Int(required=True)
    feature_enabled = graphene.Boolean()
    feature_value = graphene.String()
    feature_values = graphene.List(BranchFeatureValueInput)
    screenshots = graphene.List(BranchScreenshotInput)


class DocumentationLinkInput(graphene.InputObjectType):
    title = NimbusExperimentDocumentationLinkEnum(required=True)
    link = graphene.String(required=True)


class ReferenceBranchInput(BranchInput):
    class Meta:
        description = "The control branch"


class TreatmentBranchInput(BranchInput):
    class Meta:
        description = (
            "The treatment branch that should be in this position on the experiment."
        )


class ExperimentInput(graphene.InputObjectType):
    id = graphene.Int()
    is_rollout = graphene.Boolean()
    is_archived = graphene.Boolean()
    status = NimbusExperimentStatusEnum()
    status_next = NimbusExperimentStatusEnum()
    publish_status = NimbusExperimentPublishStatusEnum()
    name = graphene.String()
    hypothesis = graphene.String()
    application = NimbusExperimentApplicationEnum()
    public_description = graphene.String()
    is_enrollment_paused = graphene.Boolean()
    risk_mitigation_link = graphene.String()
    feature_config_id = graphene.Int()
    feature_config_ids = graphene.List(graphene.Int)
    warn_feature_schema = graphene.Boolean()
    documentation_links = graphene.List(DocumentationLinkInput)
    reference_branch = graphene.Field(ReferenceBranchInput)
    treatment_branches = graphene.List(TreatmentBranchInput)
    primary_outcomes = graphene.List(graphene.String)
    secondary_outcomes = graphene.List(graphene.String)
    channel = NimbusExperimentChannelEnum()
    firefox_min_version = NimbusExperimentFirefoxVersionEnum()
    firefox_max_version = NimbusExperimentFirefoxVersionEnum()
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
    languages = graphene.List(graphene.Int)
    conclusion_recommendation = NimbusExperimentConclusionRecommendationEnum()
    takeaways_summary = graphene.String()


class ExperimentCloneInput(graphene.InputObjectType):
    parent_slug = graphene.String(required=True)
    name = graphene.String(required=True)
    rollout_branch_slug = graphene.String()
