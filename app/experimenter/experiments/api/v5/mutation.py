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
    UpdateExperimentAudienceInput,
    UpdateExperimentBranchesInput,
    UpdateExperimentInput,
    UpdateExperimentProbeSetsInput,
    UpdateExperimentStatusInput,
)
from experimenter.experiments.api.v5.serializers import (
    NimbusAudienceUpdateSerializer,
    NimbusBranchUpdateSerializer,
    NimbusExperimentOverviewSerializer,
    NimbusProbeSetUpdateSerializer,
    NimbusStatusUpdateSerializer,
)
from experimenter.experiments.api.v5.types import NimbusExperimentType, ObjectField
from experimenter.experiments.models import NimbusExperiment


def handle_with_serializer(cls, serializer, client_mutation_id):
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
        client_mutation_id=client_mutation_id,
    )


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
        return handle_with_serializer(cls, serializer, input.client_mutation_id)


class UpdateExperimentOverview(graphene.Mutation):
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
        return handle_with_serializer(cls, serializer, input.client_mutation_id)


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
        return handle_with_serializer(cls, serializer, input.client_mutation_id)


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
            data={
                "primary_probe_sets": input["primary_probe_set_ids"],
                "secondary_probe_sets": input["secondary_probe_set_ids"],
            },
            context={"user": info.context.user},
        )
        return handle_with_serializer(cls, serializer, input.client_mutation_id)


class UpdateExperimentAudience(graphene.Mutation):
    client_mutation_id = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = UpdateExperimentAudienceInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: UpdateExperimentAudienceInput):
        experiment = NimbusExperiment.objects.get(id=input.nimbus_experiment_id)
        serializer = NimbusAudienceUpdateSerializer(
            experiment,
            data=input,
            context={"user": info.context.user},
        )
        return handle_with_serializer(cls, serializer, input.client_mutation_id)


class UpdateExperimentStatus(graphene.Mutation):
    client_mutation_id = graphene.String()
    nimbus_experiment = graphene.Field(NimbusExperimentType)
    message = ObjectField()
    status = graphene.Int()

    class Arguments:
        input = UpdateExperimentStatusInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: UpdateExperimentStatusInput):
        experiment = NimbusExperiment.objects.get(id=input.nimbus_experiment_id)
        serializer = NimbusStatusUpdateSerializer(
            experiment,
            data=input,
            context={"user": info.context.user},
        )
        return handle_with_serializer(cls, serializer, input.client_mutation_id)


class Mutation(graphene.ObjectType):
    create_experiment = CreateExperiment.Field(
        description="Create a new Nimbus Experiment."
    )
    update_experiment_overview = UpdateExperimentOverview.Field(
        description="Update a Nimbus Experiment."
    )

    update_experiment_branches = UpdateExperimentBranches.Field(
        description="Updates branches on a Nimbus Experiment."
    )

    update_experiment_probe_sets = UpdateExperimentProbeSets.Field(
        description="Updates the probesets on a Nimbus Experiment."
    )

    update_experiment_audience = UpdateExperimentAudience.Field(
        description="Updates the audience on a Nimbus Experiment."
    )

    update_experiment_status = UpdateExperimentStatus.Field(
        description="Mark a Nimubs Experiment as ready for review."
    )
