"""
This type stub file was generated by pyright.
"""

DEFAULTS = ...
DEPRECATED_SETTINGS = ...

def is_callable(value): ...

class Settings:
    def __getattr__(self, name): ...
    def get_setting(self, setting): ...
    def change_setting(self, setting, value, enter, **kwargs): ...

settings = ...
