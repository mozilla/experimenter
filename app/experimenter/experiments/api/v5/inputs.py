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
    featureConfig = graphene.Int()
    enabled = graphene.Boolean()
    value = graphene.String()


class BranchInput(graphene.InputObjectType):
    id = graphene.Int()
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    ratio = graphene.Int(required=True)
    featureEnabled = graphene.Boolean()
    featureValue = graphene.String()
    featureValues = graphene.List(BranchFeatureValueInput)
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
    isArchived = graphene.Boolean()
    status = NimbusExperimentStatusEnum()
    statusNext = NimbusExperimentStatusEnum()
    publishStatus = NimbusExperimentPublishStatusEnum()
    name = graphene.String()
    hypothesis = graphene.String()
    application = NimbusExperimentApplicationEnum()
    publicDescription = graphene.String()
    isEnrollmentPaused = graphene.Boolean()
    riskMitigationLink = graphene.String()
    featureConfigId = graphene.Int()
    featureConfigIds = graphene.List(graphene.Int)
    warnFeatureSchema = graphene.Boolean()
    documentationLinks = graphene.List(DocumentationLinkInput)
    referenceBranch = graphene.Field(ReferenceBranchInput)
    treatmentBranches = graphene.List(TreatmentBranchInput)
    primaryOutcomes = graphene.List(graphene.String)
    secondaryOutcomes = graphene.List(graphene.String)
    channel = NimbusExperimentChannelEnum()
    firefoxMinVersion = NimbusExperimentFirefoxVersionEnum()
    firefoxMaxVersion = NimbusExperimentFirefoxVersionEnum()
    populationPercent = graphene.String()
    proposedDuration = graphene.Int()
    proposedEnrollment = graphene.String()
    isSticky = graphene.Boolean()
    isFirstRun = graphene.Boolean()
    isRollout = graphene.Boolean()
    targetingConfigSlug = graphene.String()
    totalEnrolledClients = graphene.Int()
    changelogMessage = graphene.String()
    riskPartnerRelated = graphene.Boolean()
    riskRevenue = graphene.Boolean()
    riskBrand = graphene.Boolean()
    countries = graphene.List(graphene.Int)
    locales = graphene.List(graphene.Int)
    languages = graphene.List(graphene.Int)
    conclusionRecommendation = NimbusExperimentConclusionRecommendationEnum()
    takeawaysSummary = graphene.String()


class ExperimentCloneInput(graphene.InputObjectType):
    parentSlug = graphene.String(required=True)
    name = graphene.String(required=True)
    rolloutBranchSlug = graphene.String()
