"""
This type stub file was generated by pyright.
"""

from django import forms

from .fields import (
    BaseCSVField,
    BaseRangeField,
    ChoiceField,
    DateRangeField,
    DateTimeRangeField,
    IsoDateTimeField,
    IsoDateTimeRangeField,
    LookupChoiceField,
    ModelChoiceField,
    ModelMultipleChoiceField,
    MultipleChoiceField,
    RangeField,
    TimeRangeField,
)

__all__ = [
    "AllValuesFilter",
    "AllValuesMultipleFilter",
    "BaseCSVFilter",
    "BaseInFilter",
    "BaseRangeFilter",
    "BooleanFilter",
    "CharFilter",
    "ChoiceFilter",
    "DateFilter",
    "DateFromToRangeFilter",
    "DateRangeFilter",
    "DateTimeFilter",
    "DateTimeFromToRangeFilter",
    "DurationFilter",
    "Filter",
    "IsoDateTimeFilter",
    "IsoDateTimeFromToRangeFilter",
    "LookupChoiceFilter",
    "ModelChoiceFilter",
    "ModelMultipleChoiceFilter",
    "MultipleChoiceFilter",
    "NumberFilter",
    "NumericRangeFilter",
    "OrderingFilter",
    "RangeFilter",
    "TimeFilter",
    "TimeRangeFilter",
    "TypedChoiceFilter",
    "TypedMultipleChoiceFilter",
    "UUIDFilter",
]

class Filter:
    creation_counter = ...
    field_class = forms.Field
    def __init__(
        self,
        field_name=...,
        lookup_expr=...,
        *,
        label=...,
        method=...,
        distinct=...,
        exclude=...,
        **kwargs,
    ) -> None: ...
    def get_method(self, qs):
        """Return filter method based on whether we're excluding
        or simply filtering.
        """
        ...
    def method():  # -> dict[str, Any]:
        """
        Filter method needs to be lazily resolved, as it may be dependent on
        the 'parent' FilterSet.
        """
        ...
    method = ...
    def label(): ...
    label = ...
    @property
    def field(self): ...
    def filter(self, qs, value): ...

class CharFilter(Filter):
    field_class = forms.CharField

class BooleanFilter(Filter):
    field_class = forms.NullBooleanField

class ChoiceFilter(Filter):
    field_class = ChoiceField
    def __init__(self, *args, **kwargs) -> None: ...
    def filter(self, qs, value): ...

class TypedChoiceFilter(Filter):
    field_class = forms.TypedChoiceField

class UUIDFilter(Filter):
    field_class = forms.UUIDField

class MultipleChoiceFilter(Filter):
    """
    This filter performs OR(by default) or AND(using conjoined=True) query
    on the selected options.

    Advanced usage
    --------------
    Depending on your application logic, when all or no choices are selected,
    filtering may be a no-operation. In this case you may wish to avoid the
    filtering overhead, particularly if using a `distinct` call.

    You can override `get_filter_predicate` to use a custom filter.
    By default it will use the filter's name for the key, and the value will
    be the model object - or in case of passing in `to_field_name` the
    value of that attribute on the model.

    Set `always_filter` to `False` after instantiation to enable the default
    `is_noop` test. You can override `is_noop` if you need a different test
    for your application.

    `distinct` defaults to `True` as to-many relationships will generally
    require this.
    """

    field_class = MultipleChoiceField
    always_filter = ...
    def __init__(self, *args, **kwargs) -> None: ...
    def is_noop(self, qs, value):  # -> bool:
        """
        Return `True` to short-circuit unnecessary and potentially slow
        filtering.
        """
        ...
    def filter(self, qs, value): ...
    def get_filter_predicate(self, v): ...

class TypedMultipleChoiceFilter(MultipleChoiceFilter):
    field_class = forms.TypedMultipleChoiceField

class DateFilter(Filter):
    field_class = forms.DateField

class DateTimeFilter(Filter):
    field_class = forms.DateTimeField

class IsoDateTimeFilter(DateTimeFilter):
    """
    Uses IsoDateTimeField to support filtering on ISO 8601 formatted datetimes.

    For context see:

    * https://code.djangoproject.com/ticket/23448
    * https://github.com/encode/django-rest-framework/issues/1338
    * https://github.com/carltongibson/django-filter/pull/264
    """

    field_class = IsoDateTimeField

class TimeFilter(Filter):
    field_class = forms.TimeField

class DurationFilter(Filter):
    field_class = forms.DurationField

class QuerySetRequestMixin:
    """
    Add callable functionality to filters that support the ``queryset``
    argument. If the ``queryset`` is callable, then it **must** accept the
    ``request`` object as a single argument.

    This is useful for filtering querysets by properties on the ``request``
    object, such as the user.

    Example::

        def departments(request):
            company = request.user.company
            return company.department_set.all()

        class EmployeeFilter(filters.FilterSet):
            department = filters.ModelChoiceFilter(queryset=departments)
            ...

    The above example restricts the set of departments to those in the logged-in
    user's associated company.

    """

    def __init__(self, *args, **kwargs) -> None: ...
    def get_request(self): ...
    def get_queryset(self, request): ...
    @property
    def field(self): ...

class ModelChoiceFilter(QuerySetRequestMixin, ChoiceFilter):
    field_class = ModelChoiceField
    def __init__(self, *args, **kwargs) -> None: ...

class ModelMultipleChoiceFilter(QuerySetRequestMixin, MultipleChoiceFilter):
    field_class = ModelMultipleChoiceField

class NumberFilter(Filter):
    field_class = forms.DecimalField
    def get_max_validator(self):  # -> MaxValueValidator:
        """
        Return a MaxValueValidator for the field, or None to disable.
        """
        ...
    @property
    def field(self): ...

class NumericRangeFilter(Filter):
    field_class = RangeField
    def filter(self, qs, value): ...

class RangeFilter(Filter):
    field_class = RangeField
    def filter(self, qs, value): ...

class DateRangeFilter(ChoiceFilter):
    choices = ...
    filters = ...
    def __init__(self, choices=..., filters=..., *args, **kwargs) -> None: ...
    def filter(self, qs, value): ...

class DateFromToRangeFilter(RangeFilter):
    field_class = DateRangeField

class DateTimeFromToRangeFilter(RangeFilter):
    field_class = DateTimeRangeField

class IsoDateTimeFromToRangeFilter(RangeFilter):
    field_class = IsoDateTimeRangeField

class TimeRangeFilter(RangeFilter):
    field_class = TimeRangeField

class AllValuesFilter(ChoiceFilter):
    @property
    def field(self): ...

class AllValuesMultipleFilter(MultipleChoiceFilter):
    @property
    def field(self): ...

class BaseCSVFilter(Filter):
    """
    Base class for CSV type filters, such as IN and RANGE.
    """

    base_field_class = BaseCSVField
    def __init__(self, *args, **kwargs) -> None:
        class ConcreteCSVField(self.base_field_class, self.field_class): ...

class BaseInFilter(BaseCSVFilter):
    def __init__(self, *args, **kwargs) -> None: ...

class BaseRangeFilter(BaseCSVFilter):
    base_field_class = BaseRangeField
    def __init__(self, *args, **kwargs) -> None: ...

class LookupChoiceFilter(Filter):
    """
    A combined filter that allows users to select the lookup expression from a dropdown.

    * ``lookup_choices`` is an optional argument that accepts multiple input
      formats, and is ultimately normlized as the choices used in the lookup
      dropdown. See ``.get_lookup_choices()`` for more information.

    * ``field_class`` is an optional argument that allows you to set the inner
      form field class used to validate the value. Default: ``forms.CharField``

    ex::

        price = django_filters.LookupChoiceFilter(
            field_class=forms.DecimalField,
            lookup_choices=[
                ("exact", "Equals"),
                ("gt", "Greater than"),
                ("lt", "Less than"),
            ],
        )

    """

    field_class = ...
    outer_class = LookupChoiceField
    def __init__(
        self, field_name=..., lookup_choices=..., field_class=..., **kwargs
    ) -> None: ...
    @classmethod
    def normalize_lookup(cls, lookup):  # -> tuple[str, str] | tuple[Unknown, Unknown]:
        """
        Normalize the lookup into a tuple of ``(lookup expression, display value)``

        If the ``lookup`` is already a tuple, the tuple is not altered.
        If the ``lookup`` is a string, a tuple is returned with the lookup
        expression used as the basis for the display value.

        ex::

            >>> LookupChoiceFilter.normalize_lookup(('exact', 'Equals'))
            ('exact', 'Equals')

            >>> LookupChoiceFilter.normalize_lookup('has_key')
            ('has_key', 'Has key')

        """
        ...
    def get_lookup_choices(self):  # -> list[tuple[str, str] | tuple[Unknown, Unknown]]:
        """
        Get the lookup choices in a format suitable for ``django.forms.ChoiceField``.
        If the filter is initialized with ``lookup_choices``, this value is normalized
        and passed to the underlying ``LookupChoiceField``. If no choices are provided,
        they are generated from the corresponding model field's registered lookups.
        """
        ...
    @property
    def field(self): ...
    def filter(self, qs, lookup): ...

class OrderingFilter(BaseCSVFilter, ChoiceFilter):
    """
    Enable queryset ordering. As an extension of ``ChoiceFilter`` it accepts
    two additional arguments that are used to build the ordering choices.

    * ``fields`` is a mapping of {model field name: parameter name}. The
      parameter names are exposed in the choices and mask/alias the field
      names used in the ``order_by()`` call. Similar to field ``choices``,
      ``fields`` accepts the 'list of two-tuples' syntax that retains order.
      ``fields`` may also just be an iterable of strings. In this case, the
      field names simply double as the exposed parameter names.

    * ``field_labels`` is an optional argument that allows you to customize
      the display label for the corresponding parameter. It accepts a mapping
      of {field name: human readable label}. Keep in mind that the key is the
      field name, and not the exposed parameter name.

    Additionally, you can just provide your own ``choices`` if you require
    explicit control over the exposed options. For example, when you might
    want to disable descending sort options.

    This filter is also CSV-based, and accepts multiple ordering params. The
    default select widget does not enable the use of this, but it is useful
    for APIs.

    """

    descending_fmt = ...
    def __init__(self, *args, **kwargs) -> None:
        """
        ``fields`` may be either a mapping or an iterable.
        ``field_labels`` must be a map of field names to display labels
        """
        ...
    def get_ordering_value(self, param): ...
    def filter(self, qs, value): ...
    @classmethod
    def normalize_fields(
        cls, fields
    ):  # -> OrderedDict[Unknown, Unknown] | OrderedDict[str, str]:
        """
        Normalize the fields into an ordered map of {field name: param name}
        """
        ...
    def build_choices(self, fields, labels): ...

class FilterMethod:
    """
    This helper is used to override Filter.filter() when a 'method' argument
    is passed. It proxies the call to the actual method on the filter's parent.
    """

    def __init__(self, filter_instance) -> None: ...
    def __call__(self, qs, value): ...
    @property
    def method(self):  # -> Any:
        """
        Resolve the method on the parent filterset.
        """
        ...
