"""
This type stub file was generated by pyright.
"""

from .mountedtype import MountedType

class Dynamic(MountedType):
    """
    A Dynamic Type let us get the type in runtime when we generate
    the schema. So we can have lazy fields.
    """

    def __init__(self, type, with_schema=..., _creation_counter=...) -> None: ...
    def get_type(self, schema=...): ...
