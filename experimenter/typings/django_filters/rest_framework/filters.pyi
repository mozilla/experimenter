"""
This type stub file was generated by pyright.
"""

from django_filters import filters

from ..filters import *

__all__ = filters.__all__

class BooleanFilter(filters.BooleanFilter):
    def __init__(self, *args, **kwargs) -> None: ...
