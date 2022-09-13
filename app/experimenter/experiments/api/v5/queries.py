import graphene

from experimenter.experiments.api.v5.types import (
    NimbusConfigurationType,
    NimbusExperimentType,
)
from experimenter.experiments.models import NimbusExperiment


class Query(graphene.ObjectType):
    experiments = graphene.List(
        NimbusExperimentType,
        description="List Nimbus Experiments.",
    )
    experimentBySlug = graphene.Field(
        NimbusExperimentType,
        description="Retrieve a Nimbus experiment by its slug.",
        slug=graphene.String(required=True),
    )

    nimbusConfig = graphene.Field(
        NimbusConfigurationType,
        description="Nimbus Configuration Data for front-end usage.",
    )

    def resolve_experiments(root, info):
        return NimbusExperiment.objects.with_owner_features()

    def resolve_experimentBySlug(root, info, slug):
        try:
            return NimbusExperiment.objects.get(slug=slug)
        except NimbusExperiment.DoesNotExist:
            return None

    def resolve_nimbusConfig(root, info):
        return NimbusConfigurationType()
