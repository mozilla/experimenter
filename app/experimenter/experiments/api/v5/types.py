import graphene
from graphene_django.types import DjangoObjectType

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


class NimbusBranchType(DjangoObjectType):
    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment", "nimbusexperiment")


class NimbusFeatureConfigType(DjangoObjectType):
    class Meta:
        model = NimbusFeatureConfig


class NimbusExperimentType(DjangoObjectType):
    treatment_branches = graphene.List(NimbusBranchType)

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
