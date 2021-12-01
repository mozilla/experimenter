import json

import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoListField
from graphene_django.types import DjangoObjectType

from experimenter.base.models import Country, Locale
from experimenter.experiments.api.v5.serializers import NimbusExperimentReviewSerializer
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import (
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


class NimbusLocaleType(DjangoObjectType):
    id = graphene.Int()
    code = graphene.String()
    name = graphene.String()

    class Meta:
        model = Locale


class NimbusUserType(DjangoObjectType):
    id = graphene.Int()

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name", "email")


class NimbusExperimentStatus(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Status


class NimbusExperimentPublishStatus(graphene.Enum):
    class Meta:
        enum = NimbusConstants.PublishStatus


class NimbusExperimentFirefoxMinVersion(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Version


class NimbusExperimentApplication(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Application


class NimbusExperimentChannel(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Channel


class NimbusExperimentConclusionRecommendation(graphene.Enum):
    class Meta:
        enum = NimbusConstants.ConclusionRecommendation


class NimbusExperimentApplicationConfigType(graphene.ObjectType):
    application = NimbusExperimentApplication()
    channels = graphene.List(NimbusLabelValueType)
    supports_locale_country = graphene.Boolean()


class NimbusExperimentTargetingConfigType(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()
    application_values = graphene.List(graphene.String)


class NimbusFeatureConfigType(DjangoObjectType):
    id = graphene.Int()
    application = NimbusExperimentApplication()

    class Meta:
        model = NimbusFeatureConfig


class NimbusExperimentDocumentationLink(graphene.Enum):
    class Meta:
        enum = NimbusConstants.DocumentationLink


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
    feature_config = graphene.Field(NimbusFeatureConfigType)
    enabled = graphene.Boolean()
    value = graphene.String()

    class Meta:
        model = NimbusBranchFeatureValue


class NimbusBranchType(DjangoObjectType):
    id = graphene.Int(required=False)
    feature_values = DjangoListField(NimbusBranchFeatureValueType)
    screenshots = DjangoListField(NimbusBranchScreenshotType)

    class Meta:
        model = NimbusBranch
        exclude = ("experiment", "nimbusexperiment")


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
    class Meta:
        model = NimbusBucketRange
        exclude = ("id", "experiment")


class NimbusOutcomeMetricType(graphene.ObjectType):
    slug = graphene.String()
    friendly_name = graphene.String()
    description = graphene.String()


class NimbusOutcomeType(graphene.ObjectType):
    friendly_name = graphene.String()
    slug = graphene.String()
    application = NimbusExperimentApplication()
    description = graphene.String()
    isDefault = graphene.Boolean()
    metrics = graphene.List(NimbusOutcomeMetricType)


class NimbusReviewType(graphene.ObjectType):
    message = ObjectField()
    ready = graphene.Boolean()


class NimbusChangeLogType(DjangoObjectType):
    class Meta:
        model = NimbusChangeLog
        exclude = ("id",)


class NimbusSignoffRecommendationsType(graphene.ObjectType):
    qa_signoff = graphene.Boolean()
    vp_signoff = graphene.Boolean()
    legal_signoff = graphene.Boolean()


class NimbusConfigurationType(graphene.ObjectType):
    application_configs = graphene.List(NimbusExperimentApplicationConfigType)
    applications = graphene.List(NimbusLabelValueType)
    channels = graphene.List(NimbusLabelValueType)
    countries = graphene.List(NimbusCountryType)
    documentation_link = graphene.List(NimbusLabelValueType)
    feature_configs = graphene.List(NimbusFeatureConfigType)
    firefox_versions = graphene.List(NimbusLabelValueType)
    hypothesis_default = graphene.String()
    locales = graphene.List(NimbusLocaleType)
    max_primary_outcomes = graphene.Int()
    outcomes = graphene.List(NimbusOutcomeType)
    owners = graphene.List(NimbusUserType)
    targeting_configs = graphene.List(NimbusExperimentTargetingConfigType)
    conclusion_recommendations = graphene.List(NimbusLabelValueType)

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

    def resolve_application_configs(root, info):
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
                    supports_locale_country=application_config.supports_locale_country,
                )
            )
        return configs

    def resolve_feature_configs(root, info):
        return NimbusFeatureConfig.objects.all().order_by("name")

    def resolve_firefox_versions(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.Version)

    def resolve_conclusion_recommendations(root, info):
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

    def resolve_targeting_configs(root, info):
        return [
            NimbusExperimentTargetingConfigType(
                label=choice.label,
                value=choice.value,
                application_values=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].application_choice_names,
            )
            for choice in NimbusExperiment.TargetingConfig
        ]

    def resolve_hypothesis_default(root, info):
        return NimbusExperiment.HYPOTHESIS_DEFAULT

    def resolve_max_primary_outcomes(root, info):
        return NimbusExperiment.MAX_PRIMARY_OUTCOMES

    def resolve_documentation_link(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.DocumentationLink)

    def resolve_locales(root, info):
        return Locale.objects.all().order_by("name")

    def resolve_countries(root, info):
        return Country.objects.all().order_by("name")


class NimbusExperimentType(DjangoObjectType):
    id = graphene.Int()
    parent = graphene.Field(lambda: NimbusExperimentType)
    is_rollout = graphene.Boolean()
    is_archived = graphene.Boolean()
    status = NimbusExperimentStatus()
    status_next = NimbusExperimentStatus()
    publish_status = NimbusExperimentPublishStatus()
    application = NimbusExperimentApplication()
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    population_percent = graphene.String()
    channel = NimbusExperimentChannel()
    documentation_links = DjangoListField(NimbusDocumentationLinkType)
    treatment_branches = graphene.List(NimbusBranchType)
    targeting_config_slug = graphene.String()
    jexl_targeting_expression = graphene.String()
    primary_outcomes = graphene.List(graphene.String)
    secondary_outcomes = graphene.List(graphene.String)
    feature_configs = DjangoListField(NimbusFeatureConfigType)
    ready_for_review = graphene.Field(NimbusReviewType)
    monitoring_dashboard_url = graphene.String()
    results_ready = graphene.Boolean()
    start_date = graphene.DateTime()
    computed_end_date = graphene.DateTime()
    is_enrollment_paused = graphene.Boolean()
    is_enrollment_pause_pending = graphene.Boolean()
    enrollment_end_date = graphene.DateTime()
    computed_enrollment_days = graphene.Int()
    computed_duration_days = graphene.Int()
    can_edit = graphene.Boolean()
    can_archive = graphene.Boolean()
    can_review = graphene.Boolean()
    review_request = graphene.Field(NimbusChangeLogType)
    rejection = graphene.Field(NimbusChangeLogType)
    timeout = graphene.Field(NimbusChangeLogType)
    signoff_recommendations = graphene.Field(NimbusSignoffRecommendationsType)
    recipe_json = graphene.String()
    review_url = graphene.String()
    conclusion_recommendation = graphene.Field(NimbusExperimentConclusionRecommendation)

    class Meta:
        model = NimbusExperiment
        exclude = ("branches", "feature_configs")

    def resolve_reference_branch(self, info):
        if self.reference_branch:
            return self.reference_branch
        return NimbusBranch(name=NimbusConstants.DEFAULT_REFERENCE_BRANCH_NAME)

    def resolve_treatment_branches(self, info):
        if self.branches.exists():
            return self.treatment_branches
        return [NimbusBranch(name=NimbusConstants.DEFAULT_TREATMENT_BRANCH_NAME)]

    def resolve_ready_for_review(self, info):
        serializer = NimbusExperimentReviewSerializer(
            self,
            data=NimbusExperimentReviewSerializer(self).data,
        )
        ready = serializer.is_valid()
        return NimbusReviewType(message=serializer.errors, ready=ready)

    def resolve_targeting_config_slug(self, info):
        if self.targeting_config_slug in self.TargetingConfig:
            return self.TargetingConfig(self.targeting_config_slug).value
        return self.targeting_config_slug

    def resolve_jexl_targeting_expression(self, info):
        return self.targeting

    def resolve_is_enrollment_paused(self, info):
        return self.is_paused_published

    def resolve_is_enrollment_pause_pending(self, info):
        return self.is_paused and not self.is_paused_published

    def resolve_enrollment_end_date(self, info):
        return self.proposed_enrollment_end_date

    def resolve_can_edit(self, info):
        return self.can_edit

    def resolve_can_archive(self, info):
        return self.can_archive

    def resolve_can_review(self, info):
        return self.can_review(info.context.user)

    def resolve_review_request(self, info):
        return self.changes.latest_review_request()

    def resolve_rejection(self, info):
        return self.changes.latest_rejection()

    def resolve_timeout(self, info):
        return self.changes.latest_timeout()

    def resolve_recipe_json(self, info):
        return json.dumps(
            self.published_dto or NimbusExperimentSerializer(self).data,
            indent=2,
            sort_keys=True,
        )
