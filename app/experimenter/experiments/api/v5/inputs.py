import graphene

from experimenter.experiments.api.v5.types import (
    NimbusExperimentApplication,
    NimbusExperimentChannel,
    NimbusExperimentFirefoxMinVersion,
    NimbusExperimentStatus,
    NimbusExperimentTargetingConfigSlug,
)


class ExperimentInput(graphene.InputObjectType):
    client_mutation_id = graphene.String()
    name = graphene.String(required=True)
    hypothesis = graphene.String(required=True)


class CreateExperimentInput(ExperimentInput):
    name = graphene.String(required=True)
    application = NimbusExperimentApplication(required=True)


class UpdateExperimentInput(ExperimentInput):
    id = graphene.ID(required=True)
    public_description = graphene.String()


class BranchType(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    ratio = graphene.Int(required=True)
    feature_enabled = graphene.Boolean()
    feature_value = graphene.String()


class ReferenceBranchType(BranchType):
    class Meta:
        description = "The control branch"


class TreatmentBranchType(BranchType):
    class Meta:
        description = (
            "The treatment branch that should be in this position on the experiment."
        )


class UpdateExperimentBranchesInput(graphene.InputObjectType):
    client_mutation_id = graphene.String()
    nimbus_experiment_id = graphene.Int(required=True)
    feature_config_id = graphene.Int()
    reference_branch = graphene.Field(ReferenceBranchType, required=True)
    treatment_branches = graphene.List(
        TreatmentBranchType,
        required=True,
        description=(
            "List of treatment branches for this experiment. Branches will be created, "
            "updated, or deleted to match the list provided."
        ),
    )


class UpdateExperimentProbeSetsInput(graphene.InputObjectType):
    client_mutation_id = graphene.String()
    nimbus_experiment_id = graphene.Int(required=True)
    primary_probe_set_ids = graphene.List(
        graphene.Int,
        required=True,
        description="List of primary probeset ids that should be set on the experiment.",
    )
    secondary_probe_set_ids = graphene.List(
        graphene.Int,
        required=True,
        description=(
            "List of secondary probeset ids that should be set on the experiment."
        ),
    )


class UpdateExperimentAudienceInput(graphene.InputObjectType):
    client_mutation_id = graphene.String()
    nimbus_experiment_id = graphene.Int(required=True)
    channels = graphene.List(NimbusExperimentChannel)
    firefox_min_version = NimbusExperimentFirefoxMinVersion()
    population_percent = graphene.String()
    proposed_duration = graphene.Int()
    proposed_enrollment = graphene.String()
    targeting_config_slug = NimbusExperimentTargetingConfigSlug()
    total_enrolled_clients = graphene.Int()


class UpdateExperimentStatusInput(graphene.InputObjectType):
    client_mutation_id = graphene.String()
    nimbus_experiment_id = graphene.Int(required=True)
    status = NimbusExperimentStatus(required=True)
