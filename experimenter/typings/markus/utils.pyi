"""
This type stub file was generated by pyright.
"""

NONE_TYPE = ...
BAD_TAG_CHAR_REGEXP = ...

def generate_tag(key, value=...):  # -> str:
    """Generate a tag for use with the tag backends.

    The key and value (if there is one) are sanitized according to the
    following rules:

    1. after the first character, all characters must be alphanumeric,
       underscore, minus, period, or slash--invalid characters are converted
       to "_"
    2. lowercase

    If a value is provided, the final tag is `key:value`.

    The final tag must start with a letter. If it doesn't, an "a" is prepended.

    The final tag is truncated to 200 characters.

    If the final tag is "device", "host", or "source", then a "_" will be
    appended the end.

    :arg str key: the key to use
    :arg str value: the value (if any)

    :returns: the final tag

    Examples:

    >>> from markus.utils import generate_tag
    >>> generate_tag("yellow")
    'yellow'
    >>> generate_tag("rule", "is_yellow")
    'rule:is_yellow'

    Some examples of sanitizing:

    >>> from markus.utils import generate_tag
    >>> generate_tag("rule", "THIS$#$%^!@IS[]{$}GROSS!")
    'rule:this_______is_____gross_'
    >>> generate_tag("host")
    'host_'

    Example using it with :py:meth:`markus.main.MetricsInterface.incr`:

    >>> import markus
    >>> from markus.utils import generate_tag
    >>> mymetrics = markus.get_metrics(__name__)
    >>> mymetrics.incr("somekey", value=1, tags=[generate_tag("rule", "is_yellow")])

    """
    ...
