import graphene

from experimenter.experiments.api.v5.query import Query

schema = graphene.Schema(query=Query)
