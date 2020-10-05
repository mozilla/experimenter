import graphene

from experimenter.experiments.api.v5.types import NimbusExperimentType
from experimenter.experiments.models.nimbus import NimbusExperiment


class Query(graphene.ObjectType):
    experiments_by_status = graphene.Field(
        graphene.List(NimbusExperimentType),
        status=graphene.Argument(
            NimbusExperimentType._meta.fields["status"]._type, required=False
        ),
    )
    all_experiments = graphene.List(
        NimbusExperimentType,
    )
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

    def resolve_experiments_by_status(root, info, status):
        return NimbusExperiment.objects.filter(status=status).all()
