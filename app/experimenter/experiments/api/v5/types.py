import graphene
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


class NimbusBranchType(DjangoObjectType):
    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment", "nimbusexperiment")


class NimbusFeatureConfigType(DjangoObjectType):
    class Meta:
        model = NimbusFeatureConfig


class NimbusExperimentType(DjangoObjectType):
    status = NimbusExperimentStatus()
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    channels = graphene.List(NimbusExperimentChannel)
    treatment_branches = graphene.List(NimbusBranchType)
    targeting_config_slug = NimbusExperimentTargetingConfigSlug()

    class Meta:
        model = NimbusExperiment
        exclude = ("branches",)


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
