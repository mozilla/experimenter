import graphene


class ExperimentInput(graphene.InputObjectType):
    clientMutationId = graphene.String()
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
