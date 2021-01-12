"""Nimbus Experimenter Mutations

..note::

    This file contains the various mutations using the DRF serializers. While
    `django-graphene` has metaclasses that can generate these, they end up with
    a variety of GraphQL type conflicts as they all try to generate types with
    the same names. There were no docs located to explain how to reconcile this
    short of a StackOverflow post recommending this method (which works), so it
    was used:
        https://stackoverflow.com/questions/55463393/how-to-use-drf-serializers-with-graphene

"""
import graphene

from experimenter.experiments.api.v5.inputs import ExperimentInput
from experimenter.experiments.api.v5.serializers import NimbusExperimentUpdateSerializer
from experimenter.experiments.api.v5.types import NimbusExperimentType, ObjectField
from experimenter.experiments.models import NimbusExperiment


def handle_with_serializer(cls, serializer):
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
    )


class CreateExperiment(graphene.Mutation):
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = ExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: ExperimentInput):
        serializer = NimbusExperimentUpdateSerializer(
            data=input, context={"user": info.context.user}
        )
        return handle_with_serializer(cls, serializer)


class UpdateExperiment(graphene.Mutation):
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = ExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: ExperimentInput):
        exp = NimbusExperiment.objects.get(id=input.id)
        if "feature_config_id" in input:
            input["feature_config"] = input.pop("feature_config_id", None)
        serializer = NimbusExperimentUpdateSerializer(
            exp, data=input, partial=True, context={"user": info.context.user}
        )
        return handle_with_serializer(cls, serializer)


class Mutation(graphene.ObjectType):
    create_experiment = CreateExperiment.Field(
        description="Create a new Nimbus Experiment."
    )
    update_experiment = UpdateExperiment.Field(description="Update a Nimbus Experiment.")
