"""
This type stub file was generated by pyright.
"""

class JEXLException(Exception):
    """Base class for all pyjexl exceptions."""

    ...

class ParseError(JEXLException):
    """An error during the parsing of an expression."""

    ...

class InvalidOperatorError(ParseError):
    """An invalid operator was used."""

    ...

class EvaluationError(JEXLException):
    """An error during evaluation of a parsed expression."""

    ...

class MissingTransformError(EvaluationError):
    """An unregistered transform was used."""

    ...
