"""
This type stub file was generated by pyright.
"""

"""Celery Signals.

This module defines the signals (Observer pattern) sent by
both workers and clients.

Functions can be connected to these signals, and connected
functions are called whenever a signal is called.

.. seealso::

    :ref:`signals` for more information.
"""
__all__ = (
    "before_task_publish",
    "after_task_publish",
    "task_internal_error",
    "task_prerun",
    "task_postrun",
    "task_success",
    "task_received",
    "task_rejected",
    "task_unknown",
    "task_retry",
    "task_failure",
    "task_revoked",
    "celeryd_init",
    "celeryd_after_setup",
    "worker_init",
    "worker_process_init",
    "worker_process_shutdown",
    "worker_ready",
    "worker_shutdown",
    "worker_shutting_down",
    "setup_logging",
    "after_setup_logger",
    "after_setup_task_logger",
    "beat_init",
    "beat_embedded_init",
    "heartbeat_sent",
    "eventlet_pool_started",
    "eventlet_pool_preshutdown",
    "eventlet_pool_postshutdown",
    "eventlet_pool_apply",
)
before_task_publish = ...
after_task_publish = ...
task_received = ...
task_prerun = ...
task_postrun = ...
task_success = ...
task_retry = ...
task_failure = ...
task_internal_error = ...
task_revoked = ...
task_rejected = ...
task_unknown = ...
task_sent = ...
celeryd_init = ...
celeryd_after_setup = ...
import_modules = ...
worker_init = ...
worker_process_init = ...
worker_process_shutdown = ...
worker_ready = ...
worker_shutdown = ...
worker_shutting_down = ...
heartbeat_sent = ...
setup_logging = ...
after_setup_logger = ...
after_setup_task_logger = ...
beat_init = ...
beat_embedded_init = ...
eventlet_pool_started = ...
eventlet_pool_preshutdown = ...
eventlet_pool_postshutdown = ...
eventlet_pool_apply = ...
user_preload_options = ...
