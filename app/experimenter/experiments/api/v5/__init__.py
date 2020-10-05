import graphene

from experimenter.experiments.api.v5.mutation import Mutation
from experimenter.experiments.api.v5.query import Query

schema = graphene.Schema(query=Query, mutation=Mutation)
