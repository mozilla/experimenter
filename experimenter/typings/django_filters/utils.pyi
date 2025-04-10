"""
This type stub file was generated by pyright.
"""

def deprecate(msg, level_modifier=...): ...

class MigrationNotice(DeprecationWarning):
    url = ...
    def __init__(self, message) -> None: ...

class RenameAttributesBase(type):
    """
    Handles the deprecation paths when renaming an attribute.

    It does the following:
    - Defines accessors that redirect to the renamed attributes.
    - Complain whenever an old attribute is accessed.

    This is conceptually based on `django.utils.deprecation.RenameMethodsBase`.
    """

    renamed_attributes = ...
    def __new__(metacls, name, bases, attrs): ...
    def get_name(metacls, name):
        """
        Get the real attribute name. If the attribute has been renamed,
        the new name will be returned and a deprecation warning issued.
        """
        ...
    def __getattr__(metacls, name): ...
    def __setattr__(metacls, name, value): ...

def try_dbfield(fn, field_class):  # -> None:
    """
    Try ``fn`` with the DB ``field_class`` by walking its
    MRO until a result is found.

    ex::
        _try_dbfield(field_dict.get, models.CharField)

    """
    ...

def get_all_model_fields(model): ...
def get_model_field(model, field_name):  # -> None:
    """
    Get a ``model`` field, traversing relationships
    in the ``field_name``.

    ex::

        f = get_model_field(Book, "author__first_name")

    """
    ...

def get_field_parts(model, field_name):  # -> list[Unknown] | None:
    """
    Get the field parts that represent the traversable relationships from the
    base ``model`` to the final field, described by ``field_name``.

    ex::

        >>> parts = get_field_parts(Book, 'author__first_name')
        >>> [p.verbose_name for p in parts]
        ['author', 'first name']

    """
    ...

def resolve_field(
    model_field, lookup_expr
):  # -> tuple[Unknown | Field[Any, Any], Unknown | str] | None:
    """
    Resolves a ``lookup_expr`` into its final output field, given
    the initial ``model_field``. The lookup expression should only contain
    transforms and lookups, not intermediary model field parts.

    Note:
    This method is based on django.db.models.sql.query.Query.build_lookup

    For more info on the lookup API:
    https://docs.djangoproject.com/en/stable/ref/models/lookups/

    """
    ...

def handle_timezone(value, is_dst=...): ...
def verbose_field_name(
    model, field_name
):  # -> LiteralString | Literal['[invalid name]']:
    """
    Get the verbose name for a given ``field_name``. The ``field_name``
    will be traversed across relationships. Returns '[invalid name]' for
    any field name that cannot be traversed.

    ex::

        >>> verbose_field_name(Article, 'author__name')
        'author name'

    """
    ...

def verbose_lookup_expr(lookup_expr):  # -> LiteralString:
    """
    Get a verbose, more humanized expression for a given ``lookup_expr``.
    Each part in the expression is looked up in the ``FILTERS_VERBOSE_LOOKUPS``
    dictionary. Missing keys will simply default to itself.

    ex::

        >>> verbose_lookup_expr('year__lt')
        'year is less than'

        # with `FILTERS_VERBOSE_LOOKUPS = {}`
        >>> verbose_lookup_expr('year__lt')
        'year lt'

    """
    ...

def label_for_filter(model, field_name, lookup_expr, exclude=...):  # -> str | None:
    """
    Create a generic label suitable for a filter.

    ex::

        >>> label_for_filter(Article, 'author__name', 'in')
        'auther name is in'

    """
    ...

def translate_validation(error_dict):  # -> ValidationError:
    """
    Translate a Django ErrorDict into its DRF ValidationError.
    """
    ...
