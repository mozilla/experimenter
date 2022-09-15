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

from experimenter.experiments.api.v5.inputs import ExperimentCloneInput, ExperimentInput
from experimenter.experiments.api.v5.serializers import (
    NimbusExperimentCloneSerializer,
    NimbusExperimentSerializer,
)
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
        nimbusExperiment=obj,
        message=msg,
    )


class CreateExperiment(graphene.Mutation):
    nimbusExperiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()

    class Arguments:
        input = ExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: ExperimentInput):
        serializer = NimbusExperimentSerializer(
            data=input, context={"user": info.context.user}
        )
        return handle_with_serializer(cls, serializer)


class UpdateExperiment(graphene.Mutation):
    nimbusExperiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()

    class Arguments:
        input = ExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: ExperimentInput):
        experiment = NimbusExperiment.objects.get(id=input.id)
        if "featureConfigId" in input:
            input["featureConfig"] = input.pop("featureConfigId", None)
        if "featureConfigIds" in input:
            input["featureConfigs"] = input.pop("featureConfigIds", None)
        serializer = NimbusExperimentSerializer(
            experiment, data=input, partial=True, context={"user": info.context.user}
        )
        return handle_with_serializer(cls, serializer)


class CloneExperiment(graphene.Mutation):
    nimbusExperiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()

    class Arguments:
        input = ExperimentCloneInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: ExperimentInput):
        serializer = NimbusExperimentCloneSerializer(
            data=input, context={"user": info.context.user}
        )
        return handle_with_serializer(cls, serializer)


class Mutation(graphene.ObjectType):
    createExperiment = CreateExperiment.Field(
        description="Create a new Nimbus Experiment."
    )
    updateExperiment = UpdateExperiment.Field(description="Update a Nimbus Experiment.")
    cloneExperiment = CloneExperiment.Field(description="Clone an experiment.")
