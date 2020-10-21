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

from experimenter.experiments.api.v5.inputs import (
    CreateExperimentInput,
    UpdateExperimentBranchesInput,
    UpdateExperimentInput,
    UpdateExperimentProbeSetsInput,
)
from experimenter.experiments.api.v5.serializers import (
    NimbusBranchUpdateSerializer,
    NimbusExperimentOverviewSerializer,
    NimbusProbeSetUpdateSerializer,
)
from experimenter.experiments.api.v5.types import NimbusExperimentType
from experimenter.experiments.models import NimbusExperiment


class ObjectField(graphene.Scalar):
    """Utilized to serialize out Serializer errors"""

    @staticmethod
    def serialize(dt):
        return dt


class CreateExperiment(graphene.Mutation):
    client_mutation_id = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = CreateExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: CreateExperimentInput):
        serializer = NimbusExperimentOverviewSerializer(
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
            client_mutation_id=input.client_mutation_id,
        )


class UpdateExperiment(graphene.Mutation):
    client_mutation_id = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = UpdateExperimentInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: UpdateExperimentInput):
        exp = NimbusExperiment.objects.get(id=input.id)
        serializer = NimbusExperimentOverviewSerializer(
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
            client_mutation_id=input.client_mutation_id,
        )


class UpdateExperimentBranches(graphene.Mutation):
    client_mutation_id = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = UpdateExperimentBranchesInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: UpdateExperimentBranchesInput):
        exp = NimbusExperiment.objects.get(id=input.nimbus_experiment_id)
        input["feature_config"] = input.pop("feature_config_id", None)
        serializer = NimbusBranchUpdateSerializer(
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
            client_mutation_id=input.client_mutation_id,
        )


class UpdateExperimentProbeSets(graphene.Mutation):
    client_mutation_id = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = UpdateExperimentProbeSetsInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: UpdateExperimentProbeSetsInput):
        experiment = NimbusExperiment.objects.get(id=input.nimbus_experiment_id)
        serializer = NimbusProbeSetUpdateSerializer(
            experiment,
            data={"probe_sets": input["probe_set_ids"]},
            context={"user": info.context.user},
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
            client_mutation_id=input.client_mutation_id,
        )


class Mutation(graphene.ObjectType):
    create_experiment = CreateExperiment.Field(
        description="Create a new Nimbus Experiment."
    )
    update_experiment = UpdateExperiment.Field(description="Update a Nimbus Experiment.")

    update_experiment_branches = UpdateExperimentBranches.Field(
        description="Updates branches on a Nimbus Experiment."
    )

    update_experiment_probe_sets = UpdateExperimentProbeSets.Field(
        description="Updates the probesets on a Nimbus Experiment."
    )
