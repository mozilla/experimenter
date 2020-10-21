import graphene


class ExperimentInput(graphene.InputObjectType):
    client_mutation_id = graphene.String()
    name = graphene.String()
    slug = graphene.String()
    application = graphene.String()
    public_description = graphene.String()
    hypothesis = graphene.String()


class CreateExperimentInput(ExperimentInput):
    name = graphene.String(required=True)
    slug = graphene.String(required=True)


class UpdateExperimentInput(ExperimentInput):
    id = graphene.ID(required=True)


class BranchType(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    ratio = graphene.Int(required=True)
    feature_enabled = graphene.Boolean()
    feature_value = graphene.String()


class ControlBranchType(BranchType):
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
    control_branch = graphene.Field(ControlBranchType, required=True)
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
    probe_set_ids = graphene.List(
        graphene.Int,
        required=True,
        description="List of probeset ids that should be set on the experiment.",
    )
