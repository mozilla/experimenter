import graphene

from experimenter.experiments.api.v5.types import NimbusExperimentType
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import NimbusExperiment


class Query(graphene.ObjectType):
    experiments = graphene.List(
        NimbusExperimentType,
        description="List Nimbus Experiments.",
        offset=graphene.Int(),
        limit=graphene.Int(),
        status=graphene.Enum(
            "NimbusExperimentOptionalStatus", NimbusConstants.Status.choices
        )(),
    )
    experiment_by_slug = graphene.Field(
        NimbusExperimentType,
        description="Retrieve a Nimbus experiment by its slug.",
        slug=graphene.String(required=True),
    )

    def resolve_experiments(root, info, offset=0, limit=20, status=None):
        q = NimbusExperiment.objects.all()
        if status:
            q = q.filter(status=status)
        return q[offset:limit]

    def resolve_experiment_by_slug(root, info, slug):
        try:
            return NimbusExperiment.objects.get(slug=slug)
        except NimbusExperiment.DoesNotExist:
            return None
