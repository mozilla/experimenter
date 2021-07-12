import json

import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoListField
from graphene_django.types import DjangoObjectType

from experimenter.base.models import Country, Locale
from experimenter.experiments.api.v5.serializers import NimbusReadyForReviewSerializer
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusChangeLog,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
)
from experimenter.projects.models import Project


class ObjectField(graphene.Scalar):
    """Utilized to serialize out Serializer errors"""

    @staticmethod
    def serialize(dt):
        return dt


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


class NimbusUser(DjangoObjectType):
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


class NimbusExperimentChannel(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Channel


class NimbusExperimentTargetingConfigSlug(graphene.Enum):
    class Meta:
        enum = NimbusConstants.TargetingConfig


class NimbusExperimentTargetingConfigSlugChoice(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()
    application_values = graphene.List(graphene.String)


class NimbusExperimentApplication(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Application


class NimbusExperimentDocumentationLink(graphene.Enum):
    class Meta:
        enum = NimbusConstants.DocumentationLink


class NimbusBranchType(DjangoObjectType):
    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment", "nimbusexperiment")


class NimbusDocumentationLinkType(DjangoObjectType):
    class Meta:
        model = NimbusDocumentationLink
        exclude = ("id", "experiment")


class NimbusFeatureConfigType(DjangoObjectType):
    id = graphene.Int()
    application = NimbusExperimentApplication()

    class Meta:
        model = NimbusFeatureConfig


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


class NimbusOutcomeType(graphene.ObjectType):
    friendly_name = graphene.String()
    slug = graphene.String()
    application = NimbusExperimentApplication()
    description = graphene.String()


class NimbusLabelValueType(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()


class NimbusReadyForReviewType(graphene.ObjectType):
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


class NimbusExperimentType(DjangoObjectType):
    id = graphene.Int()
    status = NimbusExperimentStatus()
    status_next = NimbusExperimentStatus()
    publish_status = NimbusExperimentPublishStatus()
    application = NimbusExperimentApplication()
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    population_percent = graphene.String()
    channel = NimbusExperimentChannel()
    documentation_links = DjangoListField(NimbusDocumentationLinkType)
    treatment_branches = graphene.List(NimbusBranchType)
    targeting_config_slug = NimbusExperimentTargetingConfigSlug()
    jexl_targeting_expression = graphene.String()
    primary_outcomes = graphene.List(graphene.String)
    secondary_outcomes = graphene.List(graphene.String)
    ready_for_review = graphene.Field(NimbusReadyForReviewType)
    monitoring_dashboard_url = graphene.String()
    results_ready = graphene.Boolean()
    start_date = graphene.DateTime()
    computed_end_date = graphene.DateTime()
    is_enrollment_paused = graphene.Boolean()
    enrollment_end_date = graphene.DateTime()
    computed_enrollment_days = graphene.Int()
    computed_duration_days = graphene.Int()
    can_review = graphene.Boolean()
    review_request = graphene.Field(NimbusChangeLogType)
    rejection = graphene.Field(NimbusChangeLogType)
    timeout = graphene.Field(NimbusChangeLogType)
    signoff_recommendations = graphene.Field(NimbusSignoffRecommendationsType)
    recipe_json = graphene.String()
    review_url = graphene.String()

    class Meta:
        model = NimbusExperiment
        exclude = ("branches",)

    def resolve_reference_branch(self, info):
        return self.reference_branch

    def resolve_treatment_branches(self, info):
        if self.treatment_branches:
            return self.treatment_branches
        return [NimbusBranch(feature_enabled=False)]

    def resolve_ready_for_review(self, info):
        serializer = NimbusReadyForReviewSerializer(
            self,
            data=NimbusReadyForReviewSerializer(self).data,
        )
        ready = serializer.is_valid()
        return NimbusReadyForReviewType(message=serializer.errors, ready=ready)

    def resolve_jexl_targeting_expression(self, info):
        return self.targeting

    def resolve_is_enrollment_paused(self, info):
        return self.is_paused_published

    def resolve_enrollment_end_date(self, info):
        return self.proposed_enrollment_end_date

    def resolve_can_review(self, info):
        return self.can_review(info.context.user)

    def resolve_review_request(self, info):
        return self.changes.latest_review_request()

    def resolve_rejection(self, info):
        return self.changes.latest_rejection()

    def resolve_timeout(self, info):
        return self.changes.latest_timeout()

    def resolve_recipe_json(self, info):
        return json.dumps(NimbusExperimentSerializer(self).data, indent=2, sort_keys=True)
