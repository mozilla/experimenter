import graphene

from experimenter.experiments.api.v5.inputs import (
    CreateExperimentInput,
    UpdateExperimentInput,
)
from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.api.v5.types import NimbusExperimentType
from experimenter.experiments.models import NimbusExperiment


class ObjectField(graphene.Scalar):
    """Utilized to serialize out Serializer errors"""

    @staticmethod
    def serialize(dt):
        return dt


class CreateExperiment(graphene.Mutation):
    clientMutationId = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = CreateExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: CreateExperimentInput):
        serializer = NimbusExperimentSerializer(
            data=input, context={"user": info.context.user}
        )
        if serializer.is_valid():
            obj = serializer.save()
            msg = "success"
        else:
            msg = serializer.errors
            obj = None
        return cls(
            nimbus_experiment=obj,
            message=msg,
            status=200,
            clientMutationId=input.clientMutationId,
        )


class UpdateExperiment(graphene.Mutation):
    clientMutationId = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = UpdateExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: UpdateExperimentInput):
        exp = NimbusExperiment.objects.get(id=input.id)
        serializer = NimbusExperimentSerializer(
            exp, data=input, partial=True, context={"user": info.context.user}
        )
        if serializer.is_valid():
            obj = serializer.save()
            msg = "success"
        else:
            msg = serializer.errors
            obj = None
        return cls(
            nimbus_experiment=obj,
            message=msg,
            status=200,
            clientMutationId=input.clientMutationId,
        )


class Mutation(graphene.ObjectType):
    create_experiment = CreateExperiment.Field(
        description="Create a new Nimbus Experiment."
    )
    update_experiment = UpdateExperiment.Field(description="Update a Nimbus Experiment.")
