"""
This type stub file was generated by pyright.
"""

from celery._state import connect_on_app_finalize

"""Built-in Tasks.

The built-in tasks are always available in all app instances.
"""
__all__ = ()
logger = ...

@connect_on_app_finalize
def add_backend_cleanup_task(app):  # -> () -> None:
    """Task used to clean up expired results.

    If the configured backend requires periodic cleanup this task is also
    automatically configured to run every day at 4am (requires
    :program:`celery beat` to be running).
    """
    ...

@connect_on_app_finalize
def add_accumulate_task(
    app,
):  # -> (self: Unknown, *args: Unknown, **kwargs: Unknown) -> (Unknown | tuple[Unknown, ...]):
    """Task used by Task.replace when replacing task with group."""
    ...

@connect_on_app_finalize
def add_unlock_chord_task(
    app,
):  # -> (self: Unknown, group_id: Unknown, callback: Unknown, interval: Unknown | None = None, max_retries: Unknown | None = None, result: Unknown | None = None, Result: Unknown = app.AsyncResult, GroupResult: Unknown = app.GroupResult, result_from_tuple: (r: Unknown, app: Unknown | None = None) -> (Unknown | ResultBase) = result_from_tuple, **kwargs: Unknown) -> None:
    """Task used by result backends without native chord support.

    Will joins chord by creating a task chain polling the header
    for completion.
    """
    ...

@connect_on_app_finalize
def add_map_task(app): ...
@connect_on_app_finalize
def add_starmap_task(app): ...
@connect_on_app_finalize
def add_chunk_task(app): ...
@connect_on_app_finalize
def add_group_task(
    app,
):  # -> (self: Unknown, tasks: Unknown, result: Unknown, group_id: Unknown, partial_args: Unknown, add_to_parent: bool = True) -> (Unknown | ResultBase):
    """No longer used, but here for backwards compatibility."""
    ...

@connect_on_app_finalize
def add_chain_task(app):  # -> (*args: Unknown, **kwargs: Unknown) -> NoReturn:
    """No longer used, but here for backwards compatibility."""
    ...

@connect_on_app_finalize
def add_chord_task(
    app,
):  # -> (self: Unknown, header: Unknown, body: Unknown, partial_args: Unknown = (), interval: Unknown | None = None, countdown: int = 1, max_retries: Unknown | None = None, eager: bool = False, **kwargs: Unknown) -> Unknown:
    """No longer used, but here for backwards compatibility."""
    ...
