"""
This type stub file was generated by pyright.
"""

from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)

class GrapheneGraphQLType:
    """
    A class for extending the base GraphQLType with the related
    graphene_type
    """

    def __init__(self, *args, **kwargs) -> None: ...

class GrapheneInterfaceType(GrapheneGraphQLType, GraphQLInterfaceType): ...
class GrapheneUnionType(GrapheneGraphQLType, GraphQLUnionType): ...
class GrapheneObjectType(GrapheneGraphQLType, GraphQLObjectType): ...
class GrapheneScalarType(GrapheneGraphQLType, GraphQLScalarType): ...
class GrapheneEnumType(GrapheneGraphQLType, GraphQLEnumType): ...
class GrapheneInputObjectType(GrapheneGraphQLType, GraphQLInputObjectType): ...
