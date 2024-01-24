import graphene
from graphene_file_upload.scalars import Upload

from experimenter.experiments.api.v5.types import (
    NimbusExperimentApplicationEnum,
    NimbusExperimentChannelEnum,
    NimbusExperimentConclusionRecommendationEnum,
    NimbusExperimentDocumentationLinkEnum,
    NimbusExperimentFirefoxVersionEnum,
    NimbusExperimentPublishStatusEnum,
    NimbusExperimentQAStatusEnum,
    NimbusExperimentStatusEnum,
)


class BranchScreenshotInput(graphene.InputObjectType):
    id = graphene.Int()
    image = Upload()
    description = graphene.String()


class BranchFeatureValueInput(graphene.InputObjectType):
    feature_config = graphene.String()
    value = graphene.String()


class BranchInput(graphene.InputObjectType):
    id = graphene.Int()
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    ratio = graphene.Int(required=True)
    feature_values = graphene.List(BranchFeatureValueInput)
    screenshots = graphene.List(BranchScreenshotInput)


class DocumentationLinkInput(graphene.InputObjectType):
    title = NimbusExperimentDocumentationLinkEnum(required=True)
    link = graphene.String(required=True)


class NimbusExperimentBranchThroughRequiredInput(graphene.InputObjectType):
    required_experiment = graphene.NonNull(graphene.Int)
    branch_slug = graphene.String()


class NimbusExperimentBranchThroughExcludedInput(graphene.InputObjectType):
    excluded_experiment = graphene.NonNull(graphene.Int)
    branch_slug = graphene.String()


class ExperimentInput(graphene.InputObjectType):
    application = NimbusExperimentApplicationEnum()
    changelog_message = graphene.String()
    channel = NimbusExperimentChannelEnum()
    conclusion_recommendation = NimbusExperimentConclusionRecommendationEnum()
    countries = graphene.List(graphene.String)
    documentation_links = graphene.List(DocumentationLinkInput)
    excluded_experiments_branches = graphene.List(
        graphene.NonNull(NimbusExperimentBranchThroughExcludedInput)
    )
    feature_config_ids = graphene.List(graphene.Int)
    firefox_max_version = NimbusExperimentFirefoxVersionEnum()
    firefox_min_version = NimbusExperimentFirefoxVersionEnum()
    hypothesis = graphene.String()
    id = graphene.Int()
    is_archived = graphene.Boolean()
    is_enrollment_paused = graphene.Boolean()
    is_first_run = graphene.Boolean()
    is_localized = graphene.Boolean()
    is_rollout = graphene.Boolean()
    is_sticky = graphene.Boolean()
    languages = graphene.List(graphene.String)
    locales = graphene.List(graphene.String)
    localizations = graphene.String()
    name = graphene.String()
    population_percent = graphene.String()
    prevent_pref_conflicts = graphene.Boolean()
    primary_outcomes = graphene.List(graphene.String)
    projects = graphene.List(graphene.String)
    proposed_duration = graphene.String()
    proposed_enrollment = graphene.String()
    proposed_release_date = graphene.String()
    public_description = graphene.String()
    publish_status = NimbusExperimentPublishStatusEnum()
    qa_comment = graphene.String()
    qa_status = NimbusExperimentQAStatusEnum()
    reference_branch = graphene.Field(BranchInput)
    required_experiments_branches = graphene.List(
        graphene.NonNull(NimbusExperimentBranchThroughRequiredInput)
    )
    risk_brand = graphene.Boolean()
    risk_mitigation_link = graphene.String()
    risk_partner_related = graphene.Boolean()
    risk_revenue = graphene.Boolean()
    secondary_outcomes = graphene.List(graphene.String)
    status = NimbusExperimentStatusEnum()
    status_next = NimbusExperimentStatusEnum()
    takeaways_metric_gain = graphene.Boolean(required=False)
    takeaways_gain_amount = graphene.String()
    takeaways_qbr_learning = graphene.Boolean(required=False)
    takeaways_summary = graphene.String()
    targeting_config_slug = graphene.String()
    total_enrolled_clients = graphene.Int()
    treatment_branches = graphene.List(BranchInput)
    warn_feature_schema = graphene.Boolean()


class ExperimentCloneInput(graphene.InputObjectType):
    parent_slug = graphene.String(required=True)
    name = graphene.String(required=True)
    rollout_branch_slug = graphene.String()
