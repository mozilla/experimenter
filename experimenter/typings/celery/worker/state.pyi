"""
This type stub file was generated by pyright.
"""

import shelve

from kombu.utils.objects import cached_property

"""Internal worker state (global).

This includes the currently active and reserved tasks,
statistics, and revoked tasks.
"""
__all__ = (
    "SOFTWARE_INFO",
    "reserved_requests",
    "active_requests",
    "total_count",
    "revoked",
    "task_reserved",
    "maybe_shutdown",
    "task_accepted",
    "task_ready",
    "Persistent",
)
SOFTWARE_INFO = ...
REVOKES_MAX = ...
SUCCESSFUL_MAX = ...
REVOKE_EXPIRES = ...
SUCCESSFUL_EXPIRES = ...
requests = ...
reserved_requests = ...
active_requests = ...
successful_requests = ...
total_count = ...
all_total_count = ...
revoked = ...
should_stop = ...
should_terminate = ...

def reset_state(): ...
def maybe_shutdown():  # -> None:
    """Shutdown if flags have been set."""
    ...

def task_reserved(request, add_request=..., add_reserved_request=...):  # -> None:
    """Update global state when a task has been reserved."""
    ...

def task_accepted(
    request, _all_total_count=..., add_active_request=..., add_to_total_count=...
):  # -> None:
    """Update global state when a task has been accepted."""
    ...

def task_ready(
    request,
    successful=...,
    remove_request=...,
    discard_active_request=...,
    discard_reserved_request=...,
):  # -> None:
    """Update global state when a task is ready."""
    ...

C_BENCH = ...
C_BENCH_EVERY = ...
if C_BENCH:
    all_count = ...
    bench_first = ...
    bench_start = ...
    bench_last = ...
    bench_every = ...
    bench_sample = ...
    __reserved = ...
    __ready = ...
    def task_reserved(request):  # -> None:
        """Called when a task is reserved by the worker."""
        ...
    def task_ready(request):  # -> None:
        """Called when a task is completed."""
        ...

class Persistent:
    """Stores worker state between restarts.

    This is the persistent data stored by the worker when
    :option:`celery worker --statedb` is enabled.

    Currently only stores revoked task id's.
    """

    storage = shelve
    protocol = ...
    compress = ...
    decompress = ...
    _is_open = ...
    def __init__(self, state, filename, clock=...) -> None: ...
    def open(self): ...
    def merge(self): ...
    def sync(self): ...
    def close(self): ...
    def save(self): ...
    @cached_property
    def db(self): ...
