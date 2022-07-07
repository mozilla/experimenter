import graphene
import time

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
    experiment_by_slug = graphene.Field(
        NimbusExperimentType,
        description="Retrieve a Nimbus experiment by its slug.",
        slug=graphene.String(required=True),
    )

    nimbus_config = graphene.Field(
        NimbusConfigurationType,
        description="Nimbus Configuration Data for front-end usage.",
    )

    def resolve_experiments(root, info):
        start = time.perf_counter()
        experiments = list(NimbusExperiment.objects.latest_with_related())
        stop = time.perf_counter()
        print("\n\n\nQuery time", stop - start, "\n\n\n")
        return experiments

    def resolve_experiment_by_slug(root, info, slug):
        try:
            return NimbusExperiment.objects.get(slug=slug)
        except NimbusExperiment.DoesNotExist:
            return None

    def resolve_nimbus_config(root, info):
        return NimbusConfigurationType()
