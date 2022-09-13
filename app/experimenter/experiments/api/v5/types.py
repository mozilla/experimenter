import json

import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoListField
from graphene_django.types import DjangoObjectType

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.api.v5.serializers import NimbusReviewSerializer
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusBranchScreenshot,
    NimbusBucketRange,
    NimbusChangeLog,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
)
from experimenter.outcomes import Outcomes
from experimenter.projects.models import Project


class NimbusExperimentStatusEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Status


class NimbusExperimentPublishStatusEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.PublishStatus


class NimbusExperimentFirefoxVersionEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Version


class NimbusExperimentApplicationEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Application


class NimbusExperimentChannelEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Channel


class NimbusExperimentConclusionRecommendationEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.ConclusionRecommendation


class NimbusExperimentDocumentationLinkEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.DocumentationLink


class ObjectField(graphene.Scalar):
    """Utilized to serialize out Serializer errors"""

    @staticmethod
    def serialize(dt):
        return dt


class NimbusLabelValueType(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()


class NimbusCountryType(DjangoObjectType):
    id = graphene.Int()
    code = graphene.String()
    name = graphene.String()

    class Meta:
        model = Country
        fields = ("id", "code", "name")


class NimbusLocaleType(DjangoObjectType):
    id = graphene.Int()
    code = graphene.String()
    name = graphene.String()

    class Meta:
        model = Locale
        fields = ("id", "code", "name")


class NimbusLanguageType(DjangoObjectType):
    id = graphene.Int()
    code = graphene.String()
    name = graphene.String()

    class Meta:
        model = Language
        fields = ("id", "code", "name")


class NimbusUserType(DjangoObjectType):
    id = graphene.Int()
    firstName = graphene.String(source="first_name")
    lastName = graphene.String(source="last_name")

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "firstName", "lastName", "email")


class NimbusExperimentApplicationConfigType(graphene.ObjectType):
    application = NimbusExperimentApplicationEnum()
    channels = graphene.List(NimbusLabelValueType)


class NimbusExperimentTargetingConfigType(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()
    applicationValues = graphene.List(graphene.String)
    description = graphene.String()
    stickyRequired = graphene.Boolean()
    isFirstRunRequired = graphene.Boolean()


class NimbusFeatureConfigType(DjangoObjectType):
    id = graphene.Int()
    application = NimbusExperimentApplicationEnum()
    ownerEmail = graphene.String(source="owner_email")
    readOnly = graphene.Boolean(source="read_only")

    class Meta:
        model = NimbusFeatureConfig
        fields = (
            "slug",
            "name",
            "description",
            "application",
            "ownerEmail",
            "schema",
            "readOnly",
        )


class NimbusBranchScreenshotType(DjangoObjectType):
    id = graphene.Int()
    description = graphene.String()
    image = graphene.String()

    class Meta:
        model = NimbusBranchScreenshot

    def resolve_image(root, info):
        if root.image and root.image.name:
            return root.image.url


class NimbusBranchFeatureValueType(DjangoObjectType):
    id = graphene.Int()
    featureConfig = graphene.Field(NimbusFeatureConfigType, source="feature_config")
    enabled = graphene.Boolean()
    value = graphene.String()

    class Meta:
        model = NimbusBranchFeatureValue
        fields = ("id", "branch", "featureConfig", "enabled", "value")


class NimbusBranchType(DjangoObjectType):
    id = graphene.Int(required=False)
    featureEnabled = graphene.Boolean(required=True)
    featureValue = graphene.String(required=False)
    featureValues = graphene.List(NimbusBranchFeatureValueType)
    screenshots = DjangoListField(NimbusBranchScreenshotType)

    class Meta:
        model = NimbusBranch
        fields = (
            "slug",
            "name",
            "description",
            "ratio",
            "screenshots",
            "featureEnabled",
            "featureValue",
            "featureValues",
        )

    def resolve_featureValues(root, info):
        return root.feature_values.all()

    def resolve_featureEnabled(root, info):
        return (
            root.feature_values.exists()
            and root.feature_values.all().order_by("feature_config__slug").first().enabled
        )

    def resolve_featureValue(root, info):
        return (
            root.feature_values.exists()
            and root.feature_values.all().order_by("feature_config__slug").first().value
        ) or ""


class NimbusDocumentationLinkType(DjangoObjectType):
    class Meta:
        model = NimbusDocumentationLink
        exclude = ("id", "experiment")


class ProjectType(DjangoObjectType):
    id = graphene.Int()

    class Meta:
        model = Project


class NimbusIsolationGroupType(DjangoObjectType):
    class Meta:
        model = NimbusIsolationGroup
        exclude = ("id",)


class NimbusBucketRangeType(DjangoObjectType):
    isolationGroup = graphene.Field(NimbusIsolationGroupType, source="isolation_group")

    class Meta:
        model = NimbusBucketRange
        fields = ("isolationGroup", "start", "end", "count")


class NimbusOutcomeMetricType(graphene.ObjectType):
    slug = graphene.String()
    friendlyName = graphene.String(source="friendly_name")
    description = graphene.String()


class NimbusOutcomeType(graphene.ObjectType):
    friendlyName = graphene.String(source="friendly_name")
    slug = graphene.String()
    application = NimbusExperimentApplicationEnum()
    description = graphene.String()
    isDefault = graphene.Boolean(source="is_default")
    metrics = graphene.List(NimbusOutcomeMetricType)


class NimbusReviewType(graphene.ObjectType):
    message = ObjectField()
    warnings = ObjectField()
    ready = graphene.Boolean()


class NimbusChangeLogType(DjangoObjectType):
    changedOn = graphene.DateTime(source="changed_on", required=True)
    changedBy = graphene.Field(NimbusUserType, source="changed_by", required=True)
    oldStatus = NimbusExperimentStatusEnum(source="old_status")
    oldStatusNext = NimbusExperimentStatusEnum(source="old_status_next")
    oldPublishStatus = NimbusExperimentPublishStatusEnum(source="old_publish_status")
    newStatus = NimbusExperimentStatusEnum(source="new_status")
    newStatusNext = NimbusExperimentStatusEnum(source="new_status_next")
    newPublishStatus = NimbusExperimentPublishStatusEnum(source="old_publish_status")
    experimentData = graphene.JSONString(source="experiment_data")
    publishedDtoChanged = graphene.Boolean(source="published_dto_changed")

    class Meta:
        model = NimbusChangeLog
        fields = (
            "experiment",
            "changedOn",
            "changedBy",
            "oldStatus",
            "oldStatusNext",
            "oldPublishStatus",
            "newStatus",
            "newStatusNext",
            "newPublishStatus",
            "experimentData",
            "publishedDtoChanged",
            "message",
        )


class NimbusSignoffRecommendationsType(graphene.ObjectType):
    qaSignoff = graphene.Boolean()
    vpSignoff = graphene.Boolean()
    legalSignoff = graphene.Boolean()


class NimbusConfigurationType(graphene.ObjectType):
    applicationConfigs = graphene.List(NimbusExperimentApplicationConfigType)
    applications = graphene.List(NimbusLabelValueType)
    channels = graphene.List(NimbusLabelValueType)
    countries = graphene.List(NimbusCountryType)
    documentationLink = graphene.List(NimbusLabelValueType)
    allFeatureConfigs = graphene.List(NimbusFeatureConfigType)
    firefoxVersions = graphene.List(NimbusLabelValueType)
    hypothesisDefault = graphene.String()
    locales = graphene.List(NimbusLocaleType)
    languages = graphene.List(NimbusLanguageType)
    maxPrimaryOutcomes = graphene.Int()
    outcomes = graphene.List(NimbusOutcomeType)
    owners = graphene.List(NimbusUserType)
    targetingConfigs = graphene.List(NimbusExperimentTargetingConfigType)
    conclusionRecommendations = graphene.List(NimbusLabelValueType)

    def _text_choices_to_label_value_list(root, text_choices):
        return [
            NimbusLabelValueType(
                label=text_choices[name].label,
                value=name,
            )
            for name in text_choices.names
        ]

    def resolve_applications(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.Application)

    def resolve_channels(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.Channel)

    def resolve_applicationConfigs(root, info):
        configs = []
        for application in NimbusExperiment.Application:
            application_config = NimbusExperiment.APPLICATION_CONFIGS[application]
            configs.append(
                NimbusExperimentApplicationConfigType(
                    application=application,
                    channels=[
                        NimbusLabelValueType(label=channel.label, value=channel.name)
                        for channel in NimbusExperiment.Channel
                        if channel in application_config.channel_app_id
                    ],
                )
            )
        return configs

    def resolve_allFeatureConfigs(root, info):
        return NimbusFeatureConfig.objects.all().order_by("name")

    def resolve_firefoxVersions(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.Version)

    def resolve_conclusionRecommendations(root, info):
        return root._text_choices_to_label_value_list(
            NimbusExperiment.ConclusionRecommendation
        )

    def resolve_outcomes(root, info):
        return Outcomes.all()

    def resolve_owners(root, info):
        return (
            get_user_model()
            .objects.filter(owned_nimbusexperiments__isnull=False)
            .distinct()
            .order_by("email")
        )

    def resolve_targetingConfigs(root, info):
        return [
            NimbusExperimentTargetingConfigType(
                label=choice.label,
                value=choice.value,
                applicationValues=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].application_choice_names,
                description=NimbusExperiment.TARGETING_CONFIGS[choice.value].description,
                stickyRequired=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].sticky_required,
                isFirstRunRequired=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].is_first_run_required,
            )
            for choice in NimbusExperiment.TargetingConfig
        ]

    def resolve_hypothesisDefault(root, info):
        return NimbusExperiment.HYPOTHESIS_DEFAULT

    def resolve_maxPrimaryOutcomes(root, info):
        return NimbusExperiment.MAX_PRIMARY_OUTCOMES

    def resolve_documentationLink(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.DocumentationLink)

    def resolve_locales(root, info):
        return Locale.objects.all().order_by("name")

    def resolve_countries(root, info):
        return Country.objects.all().order_by("name")

    def resolve_languages(root, info):
        return Language.objects.all().order_by("name")


class NimbusExperimentType(DjangoObjectType):
    id = graphene.Int()
    parent = graphene.Field(lambda: NimbusExperimentType)
    isRollout = graphene.Boolean(source="is_rollout")
    isArchived = graphene.Boolean(source="is_archived")
    status = NimbusExperimentStatusEnum()
    statusNext = NimbusExperimentStatusEnum(source="status_next")
    publishStatus = NimbusExperimentPublishStatusEnum(source="publish_status")
    application = NimbusExperimentApplicationEnum()
    firefoxMinVersion = NimbusExperimentFirefoxVersionEnum(source="firefox_min_version")
    firefoxMaxVersion = NimbusExperimentFirefoxVersionEnum(source="firefox_min_version")
    populationPercent = graphene.String(source="population_percent")
    channel = NimbusExperimentChannelEnum()
    documentationLinks = DjangoListField(
        NimbusDocumentationLinkType, source="documentation_links"
    )
    referenceBranch = graphene.Field(NimbusBranchType)
    treatmentBranches = graphene.List(NimbusBranchType)
    targetingConfigSlug = graphene.String()
    targetingConfig = graphene.List(NimbusExperimentTargetingConfigType)
    isSticky = graphene.Boolean(source="is_sticky")
    isFirstRun = graphene.Boolean(source="is_first_run", required=True)
    jexlTargetingExpression = graphene.String(source="targeting")
    primaryOutcomes = graphene.List(graphene.String, source="primary_outcomes")
    secondaryOutcomes = graphene.List(graphene.String, source="secondary_outcomes")
    featureConfig = graphene.Field(NimbusFeatureConfigType)
    featureConfigs = graphene.List(NimbusFeatureConfigType)
    warnFeatureSchema = graphene.Boolean(source="warn_feature_schema")
    readyForReview = graphene.Field(NimbusReviewType)
    monitoringDashboardUrl = graphene.String(source="monitoring_dashboard_url")
    resultsReady = graphene.Boolean(source="results_ready")
    startDate = graphene.DateTime(source="start_date")
    computedEndDate = graphene.DateTime(source="computed_end_date")
    isEnrollmentPaused = graphene.Boolean(source="is_paused_published")
    isEnrollmentPausePending = graphene.Boolean()
    enrollmentEndDate = graphene.DateTime(source="proposed_enrollment_end_date")
    computedEnrollmentDays = graphene.Int(source="computed_enrollment_days")
    computedDurationDays = graphene.Int(source="computed_duration_days")
    canEdit = graphene.Boolean(source="can_edit")
    canArchive = graphene.Boolean(source="can_archive")
    canReview = graphene.Boolean()
    reviewRequest = graphene.Field(NimbusChangeLogType)
    rejection = graphene.Field(NimbusChangeLogType)
    timeout = graphene.Field(NimbusChangeLogType)
    signoffRecommendations = graphene.Field(
        NimbusSignoffRecommendationsType, source="signoff_recommendations"
    )
    recipeJson = graphene.String()
    reviewUrl = graphene.String(source="review_url")
    conclusionRecommendation = graphene.Field(
        NimbusExperimentConclusionRecommendationEnum,
        source="conclusion_recommendation",
    )
    publicDescription = graphene.String(source="public_description", required=True)
    riskMitigationLink = graphene.String(source="risk_mitigation_link", required=True)
    rolloutMonitoringDashboardUrl = graphene.String(
        source="rollout_monitoring_dashboard_url"
    )
    takeawaysSummary = graphene.String(source="takeaways_summary")
    totalEnrolledClients = graphene.Int(source="total_enrolled_clients", required=True)
    proposedEnrollment = graphene.Int(source="proposed_enrollment", required=True)
    proposedDuration = graphene.Int(source="proposed_duration", required=True)
    riskRevenue = graphene.Boolean(source="risk_revenue")
    riskBrand = graphene.Boolean(source="risk_brand")
    riskPartnerRelated = graphene.Boolean(source="risk_partner_related")

    class Meta:
        model = NimbusExperiment
        fields = (
            "id",
            "parent",
            "slug",
            "name",
            "hypothesis",
            "owner",
            "locales",
            "countries",
            "languages",
            "isRollout",
            "isArchived",
            "status",
            "statusNext",
            "publishStatus",
            "application",
            "firefoxMinVersion",
            "firefoxMaxVersion",
            "populationPercent",
            "channel",
            "documentationLinks",
            "referenceBranch",
            "treatmentBranches",
            "targetingConfigSlug",
            "targetingConfig",
            "isSticky",
            "isFirstRun",
            "jexlTargetingExpression",
            "primaryOutcomes",
            "secondaryOutcomes",
            "featureConfig",
            "featureConfigs",
            "warnFeatureSchema",
            "readyForReview",
            "monitoringDashboardUrl",
            "resultsReady",
            "startDate",
            "computedEndDate",
            "isEnrollmentPaused",
            "isEnrollmentPausePending",
            "enrollmentEndDate",
            "computedEnrollmentDays",
            "computedDurationDays",
            "canEdit",
            "canArchive",
            "canReview",
            "reviewRequest",
            "rejection",
            "timeout",
            "signoffRecommendations",
            "recipeJson",
            "reviewUrl",
            "conclusionRecommendation",
            "publicDescription",
            "riskMitigationLink",
            "rolloutMonitoringDashboardUrl",
            "takeawaysSummary",
            "totalEnrolledClients",
            "proposedEnrollment",
            "proposedDuration",
            "riskRevenue",
            "riskBrand",
            "riskPartnerRelated",
        )

    def resolve_featureConfig(self, info):
        if self.feature_configs.exists():
            return sorted(
                self.feature_configs.all(),
                key=lambda feature_config: (feature_config.slug),
            )[0]

    def resolve_featureConfigs(self, info):
        return self.feature_configs.all()

    def resolve_referenceBranch(self, info):
        if self.reference_branch:
            return self.reference_branch
        return NimbusBranch(name=NimbusConstants.DEFAULT_REFERENCE_BRANCH_NAME)

    def resolve_treatmentBranches(self, info):
        if self.branches.exists():
            return self.treatment_branches
        return [NimbusBranch(name=NimbusConstants.DEFAULT_TREATMENT_BRANCH_NAME)]

    def resolve_readyForReview(self, info):
        serializer = NimbusReviewSerializer(
            self,
            data=NimbusReviewSerializer(self).data,
        )
        ready = serializer.is_valid()
        return NimbusReviewType(
            message=serializer.errors,
            warnings=serializer.warnings,
            ready=ready,
        )

    def resolve_targetingConfigSlug(self, info):
        if self.targeting_config_slug in self.TargetingConfig:
            return self.TargetingConfig(self.targeting_config_slug).value
        return self.targeting_config_slug

    def resolve_targetingConfig(self, info):
        targeting_config = NimbusExperiment.TARGETING_CONFIGS[self.targeting_config_slug]
        return [
            NimbusExperimentTargetingConfigType(
                label=targeting_config.name,
                value=self.targeting_config_slug,
                description=targeting_config.description,
                applicationValues=targeting_config.application_choice_names,
                stickyRequired=targeting_config.sticky_required,
                isFirstRunRequired=targeting_config.is_first_run_required,
            )
        ]

    def resolve_isEnrollmentPausePending(self, info):
        return self.is_paused and not self.is_paused_published

    def resolve_canReview(self, info):
        return self.can_review(info.context.user)

    def resolve_reviewRequest(self, info):
        return self.changes.latest_review_request()

    def resolve_rejection(self, info):
        return self.changes.latest_rejection()

    def resolve_timeout(self, info):
        return self.changes.latest_timeout()

    def resolve_recipeJson(self, info):
        return json.dumps(
            self.published_dto or NimbusExperimentSerializer(self).data,
            indent=2,
            sort_keys=True,
        )
