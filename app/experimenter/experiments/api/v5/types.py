import graphene
from django.contrib.auth import get_user_model
from graphene_django.types import DjangoObjectType

from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
    NimbusProbe,
    NimbusProbeSet,
)
from experimenter.projects.models import Project


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


class NimbusBranchType(DjangoObjectType):
    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment", "nimbusexperiment")


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


class NimbusExperimentType(DjangoObjectType):
    status = NimbusExperimentStatus()
    application = NimbusExperimentApplication()
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    channels = graphene.List(NimbusExperimentChannel)
    treatment_branches = graphene.List(NimbusBranchType)
    targeting_config_slug = NimbusExperimentTargetingConfigSlug()
    primary_probe_sets = graphene.List(NimbusProbeSetType)
    secondary_probe_sets = graphene.List(NimbusProbeSetType)

    class Meta:
        model = NimbusExperiment
        exclude = ("branches", "probe_sets")
