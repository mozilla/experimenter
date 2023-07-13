import graphene

from experimenter.experiments.api.v5.types import (
    NimbusConfigurationType,
    NimbusExperimentApplicationEnum,
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
    experiments_by_application = graphene.NonNull(
        graphene.List(graphene.NonNull(NimbusExperimentType)),
        description="List Nimbus Experiments by application.",
        application=NimbusExperimentApplicationEnum(required=True),
    )

    nimbus_config = graphene.Field(
        NimbusConfigurationType,
        description="Nimbus Configuration Data for front-end usage.",
    )

    def resolve_experiments(self, info):
        return NimbusExperiment.objects.with_owner_features()

    def resolve_experiment_by_slug(self, info, slug):
        try:
            return NimbusExperiment.objects.get(slug=slug)
        except NimbusExperiment.DoesNotExist:
            return None

    def resolve_experiments_by_application(self, info, application):
        return NimbusExperiment.objects.filter(application=application)

    def resolve_nimbus_config(self, info):
        return NimbusConfigurationType()
