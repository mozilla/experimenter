import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoListField
from graphene_django.types import DjangoObjectType

from experimenter.experiments.api.v5.serializers import NimbusReadyForReviewSerializer
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import (
    NimbusBranch,
    NimbusBucketRange,
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
    class Meta:
        model = NimbusFeatureConfig


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project


class NimbusIsolationGroupType(DjangoObjectType):
    class Meta:
        model = NimbusIsolationGroup


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


class NimbusExperimentOwner(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name", "email")


class NimbusReadyForReviewType(graphene.ObjectType):
    message = ObjectField()
    ready = graphene.Boolean()


class NimbusExperimentType(DjangoObjectType):
    id = graphene.Int()
    status = NimbusExperimentStatus()
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
    start_date = graphene.DateTime()
    computed_end_date = graphene.DateTime()
    is_enrollment_paused = graphene.Boolean()
    enrollment_end_date = graphene.DateTime()

    class Meta:
        model = NimbusExperiment
        exclude = ("branches",)

    def resolve_reference_branch(self, info):
        if self.reference_branch:
            return self.reference_branch
        return NimbusBranch(feature_enabled=False)

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
        return self.is_paused

    def resolve_enrollment_end_date(self, info):
        return self.proposed_enrollment_end_date
