"""
This type stub file was generated by pyright.
"""

from contextlib import contextmanager

"""Utilities for debugging memory usage, blocking calls, etc."""
__all__ = (
    "blockdetection",
    "sample_mem",
    "memdump",
    "sample",
    "humanbytes",
    "mem_rss",
    "ps",
    "cry",
)
UNITS = ...
_process = ...
_mem_sample = ...

@contextmanager
def blockdetection(timeout):  # -> Generator[None, None, None]:
    """Context that raises an exception if process is blocking.

    Uses ``SIGALRM`` to detect blocking functions.
    """
    ...

def sample_mem():  # -> str | None:
    """Sample RSS memory usage.

    Statistics can then be output by calling :func:`memdump`.
    """
    ...

def memdump(samples=..., file=...):  # -> None:
    """Dump memory statistics.

    Will print a sample of all RSS memory samples added by
    calling :func:`sample_mem`, and in addition print
    used RSS memory after :func:`gc.collect`.
    """
    ...

def sample(x, n, k=...):  # -> Generator[Unknown, None, None]:
    """Given a list `x` a sample of length ``n`` of that list is returned.

    For example, if `n` is 10, and `x` has 100 items, a list of every tenth.
    item is returned.

    ``k`` can be used as offset.
    """
    ...

def hfloat(f, p=...):  # -> int | str:
    """Convert float to value suitable for humans.

    Arguments:
        f (float): The floating point number.
        p (int): Floating point precision (default is 5).
    """
    ...

def humanbytes(s):  # -> str:
    """Convert bytes to human-readable form (e.g., KB, MB)."""
    ...

def mem_rss():  # -> str | None:
    """Return RSS memory usage as a humanized string."""
    ...

def ps():  # -> Process | None:
    """Return the global :class:`psutil.Process` instance.

    Note:
        Returns :const:`None` if :pypi:`psutil` is not installed.
    """
    ...

def cry(out=..., sepchr=..., seplen=...):  # -> str:
    """Return stack-trace of all active threads.

    See Also:
        Taken from https://gist.github.com/737056.
    """
    ...
