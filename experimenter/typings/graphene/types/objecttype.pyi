"""
This type stub file was generated by pyright.
"""

from typing import Dict, Iterable, Type

from .base import BaseOptions, BaseType
from .field import Field
from .interface import Interface

MYPY = ...
if MYPY: ...

class ObjectTypeOptions(BaseOptions):
    fields: Dict[str, Field] = ...
    interfaces: Iterable[Type[Interface]] = ...

class ObjectType(BaseType):
    """
    Object Type Definition

    Almost all of the GraphQL types you define will be object types. Object types
    have a name, but most importantly describe their fields.

    The name of the type defined by an _ObjectType_ defaults to the class name. The type
    description defaults to the class docstring. This can be overriden by adding attributes
    to a Meta inner class.

    The class attributes of an _ObjectType_ are mounted as instances of ``graphene.Field``.

    Methods starting with ``resolve_<field_name>`` are bound as resolvers of the matching Field
    name. If no resolver is provided, the default resolver is used.

    Ambiguous types with Interface and Union can be determined through``is_type_of`` method and
    ``Meta.possible_types`` attribute.

    .. code:: python

        from graphene import ObjectType, String, Field

        class Person(ObjectType):
            class Meta:
                description = 'A human'

            # implicitly mounted as Field
            first_name = String()
            # explicitly mounted as Field
            last_name = Field(String)

            def resolve_last_name(parent, info):
                return last_name

    ObjectType must be mounted using ``graphene.Field``.

    .. code:: python

        from graphene import ObjectType, Field

        class Query(ObjectType):

            person = Field(Person, description="My favorite person")

    Meta class options (optional):
        name (str): Name of the GraphQL type (must be unique in schema). Defaults to class
            name.
        description (str): Description of the GraphQL type in the schema. Defaults to class
            docstring.
        interfaces (Iterable[graphene.Interface]): GraphQL interfaces to extend with this object.
            all fields from interface will be included in this object's schema.
        possible_types (Iterable[class]): Used to test parent value object via isintance to see if
            this type can be used to resolve an ambigous type (interface, union).
        default_resolver (any Callable resolver): Override the default resolver for this
            type. Defaults to graphene default resolver which returns an attribute or dictionary
            key with the same name as the field.
        fields (Dict[str, graphene.Field]): Dictionary of field name to Field. Not recommended to
            use (prefer class attributes).

    An _ObjectType_ can be used as a simple value object by creating an instance of the class.

    .. code:: python

        p = Person(first_name='Bob', last_name='Roberts')
        assert p.first_name == 'Bob'

    Args:
        *args (List[Any]): Positional values to use for Field values of value object
        **kwargs (Dict[str: Any]): Keyword arguments to use for Field values of value object
    """

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=...,
        possible_types=...,
        default_resolver=...,
        _meta=...,
        **options,
    ): ...
    is_type_of = ...
    def __init__(self, *args, **kwargs) -> None: ...
