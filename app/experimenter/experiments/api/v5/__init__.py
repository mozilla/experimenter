import graphene

from experimenter.experiments.api.v5.mutations import Mutation
from experimenter.experiments.api.v5.queries import Query

schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
