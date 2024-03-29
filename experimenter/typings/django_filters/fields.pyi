"""
This type stub file was generated by pyright.
"""

from collections import namedtuple

from django import forms

from .widgets import BaseCSVWidget, CSVWidget, DateRangeWidget, RangeWidget

class RangeField(forms.MultiValueField):
    widget = RangeWidget
    def __init__(self, fields=..., *args, **kwargs) -> None: ...
    def compress(self, data_list): ...

class DateRangeField(RangeField):
    widget = DateRangeWidget
    def __init__(self, *args, **kwargs) -> None: ...
    def compress(self, data_list): ...

class DateTimeRangeField(RangeField):
    widget = DateRangeWidget
    def __init__(self, *args, **kwargs) -> None: ...

class IsoDateTimeRangeField(RangeField):
    widget = DateRangeWidget
    def __init__(self, *args, **kwargs) -> None: ...

class TimeRangeField(RangeField):
    widget = DateRangeWidget
    def __init__(self, *args, **kwargs) -> None: ...

class Lookup(namedtuple("Lookup", ("value", "lookup_expr"))):
    def __new__(cls, value, lookup_expr): ...

class LookupChoiceField(forms.MultiValueField):
    default_error_messages = ...
    def __init__(self, field, lookup_choices, *args, **kwargs) -> None: ...
    def compress(self, data_list): ...

class IsoDateTimeField(forms.DateTimeField):
    """
    Supports 'iso-8601' date format too which is out the scope of
    the ``datetime.strptime`` standard library

    # ISO 8601: ``http://www.w3.org/TR/NOTE-datetime``

    Based on Gist example by David Medina https://gist.github.com/copitux/5773821
    """

    ISO_8601 = ...
    input_formats = ...
    def strptime(self, value, format): ...

class BaseCSVField(forms.Field):
    """
    Base field for validating CSV types. Value validation is performed by
    secondary base classes.

    ex::
        class IntegerCSVField(BaseCSVField, filters.IntegerField):
            pass

    """

    base_widget_class = BaseCSVWidget
    def __init__(self, *args, **kwargs) -> None: ...
    def clean(self, value): ...

class BaseRangeField(BaseCSVField):
    widget = CSVWidget
    default_error_messages = ...
    def clean(self, value): ...

class ChoiceIterator:
    def __init__(self, field, choices) -> None: ...
    def __iter__(self): ...
    def __len__(self): ...

class ModelChoiceIterator(forms.models.ModelChoiceIterator):
    def __iter__(self): ...
    def __len__(self): ...

class ChoiceIteratorMixin:
    def __init__(self, *args, **kwargs) -> None: ...
    choices = ...

class ChoiceField(ChoiceIteratorMixin, forms.ChoiceField):
    iterator = ChoiceIterator
    def __init__(self, *args, **kwargs) -> None: ...

class MultipleChoiceField(ChoiceIteratorMixin, forms.MultipleChoiceField):
    iterator = ChoiceIterator
    def __init__(self, *args, **kwargs) -> None: ...

class ModelChoiceField(ChoiceIteratorMixin, forms.ModelChoiceField):
    iterator = ...
    def to_python(self, value): ...

class ModelMultipleChoiceField(ChoiceIteratorMixin, forms.ModelMultipleChoiceField):
    iterator = ...
