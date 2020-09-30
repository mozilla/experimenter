import graphene

from experimenter.experiments.api.v5.types import NimbusExperimentType
from experimenter.experiments.models.nimbus import NimbusExperiment


class Query(graphene.ObjectType):
    all_experiments = graphene.List(NimbusExperimentType)
    experiment_by_slug = graphene.Field(
        NimbusExperimentType, slug=graphene.String(required=True)
    )

    def resolve_all_experiments(root, info):
        return NimbusExperiment.objects.all()

    def resolve_experiment_by_slug(root, info, slug):
        try:
            return NimbusExperiment.objects.get(slug=slug)
        except NimbusExperiment.DoesNotExist:
            return None
