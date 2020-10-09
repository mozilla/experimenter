from graphene_django.types import DjangoObjectType

from experimenter.experiments.models.nimbus import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
)
from experimenter.projects.models import Project


class NimbusBranchType(DjangoObjectType):
    class Meta:
        model = NimbusBranch
        exclude = ("id", "experiment", "nimbusexperiment")


class NimbusExperimentType(DjangoObjectType):
    class Meta:
        model = NimbusExperiment
        exclude = ("id",)


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        exclude = ("id",)


class NimbusIsolationGroupType(DjangoObjectType):
    class Meta:
        model = NimbusIsolationGroup
        exclude = ("id",)


class NimbusBucketRangeType(DjangoObjectType):
    class Meta:
        model = NimbusBucketRange
        exclude = ("id", "experiment")


class NimbusFeatureConfigType(DjangoObjectType):
    class Meta:
        model = NimbusFeatureConfig
