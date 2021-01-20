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
    NimbusProbe,
    NimbusProbeSet,
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


class NimbusProbeType(DjangoObjectType):
    class Meta:
        model = NimbusProbe


class NimbusProbeSetType(DjangoObjectType):
    class Meta:
        model = NimbusProbeSet


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
    application = NimbusExperimentApplication()
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    population_percent = graphene.String()
    channel = NimbusExperimentChannel()
    documentation_links = DjangoListField(NimbusDocumentationLinkType)
    treatment_branches = graphene.List(NimbusBranchType)
    targeting_config_slug = NimbusExperimentTargetingConfigSlug()
    targeting_config_targeting = graphene.String()
    primary_probe_sets = graphene.List(NimbusProbeSetType)
    secondary_probe_sets = graphene.List(NimbusProbeSetType)
    ready_for_review = graphene.Field(NimbusReadyForReviewType)
    monitoring_dashboard_url = graphene.String()
    start_date = graphene.DateTime()
    end_date = graphene.DateTime()

    class Meta:
        model = NimbusExperiment
        exclude = ("branches", "probe_sets")

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
            data=NimbusReadyForReviewSerializer(
                self,
            ).data,
        )
        ready = serializer.is_valid()
        return NimbusReadyForReviewType(message=serializer.errors, ready=ready)

    def resolve_targeting_config_targeting(self, info):
        targeting_config = self.TARGETING_CONFIGS.get(self.targeting_config_slug, None)
        if targeting_config:
            return targeting_config.targeting
        else:
            return ""
