"""
This type stub file was generated by pyright.
"""

from collections import UserList

from kombu.utils.objects import cached_property

"""Start/stop/manage workers."""
__all__ = ("Cluster", "Node")
CELERY_EXE = ...

def celery_exe(*args): ...
def build_nodename(name, prefix, suffix): ...
def build_expander(nodename, shortname, hostname): ...
def format_opt(opt, value): ...

class NamespacedOptionParser:
    def __init__(self, args) -> None: ...
    def parse(self): ...
    def process_long_opt(self, arg, value=...): ...
    def process_short_opt(self, arg, value=...): ...
    def optmerge(self, ns, defaults=...): ...
    def add_option(self, name, value, short=..., ns=...): ...

class Node:
    """Represents a node in a cluster."""

    def __init__(
        self, name, cmd=..., append=..., options=..., extra_args=...
    ) -> None: ...
    def alive(self): ...
    def send(self, sig, on_error=...): ...
    def start(self, env=..., **kwargs): ...
    def handle_process_exit(self, retcode, on_signalled=..., on_failure=...): ...
    def prepare_argv(self, argv, path): ...
    def getopt(self, *alt): ...
    def __repr__(self): ...
    @cached_property
    def pidfile(self): ...
    @cached_property
    def logfile(self): ...
    @property
    def pid(self): ...
    @pid.setter
    def pid(self, value): ...
    @cached_property
    def executable(self): ...
    @cached_property
    def argv_with_executable(self): ...
    @classmethod
    def from_kwargs(cls, name, **kwargs): ...

def maybe_call(fun, *args, **kwargs): ...

class MultiParser:
    Node = Node
    def __init__(
        self, cmd=..., append=..., prefix=..., suffix=..., range_prefix=...
    ) -> None: ...
    def parse(self, p): ...

class Cluster(UserList):
    """Represent a cluster of workers."""

    def __init__(
        self,
        nodes,
        cmd=...,
        env=...,
        on_stopping_preamble=...,
        on_send_signal=...,
        on_still_waiting_for=...,
        on_still_waiting_progress=...,
        on_still_waiting_end=...,
        on_node_start=...,
        on_node_restart=...,
        on_node_shutdown_ok=...,
        on_node_status=...,
        on_node_signal=...,
        on_node_signal_dead=...,
        on_node_down=...,
        on_child_spawn=...,
        on_child_signalled=...,
        on_child_failure=...,
    ) -> None: ...
    def start(self): ...
    def start_node(self, node): ...
    def send_all(self, sig): ...
    def kill(self): ...
    def restart(self, sig=...): ...
    def stop(self, retry=..., callback=..., sig=...): ...
    def stopwait(self, retry=..., callback=..., sig=...): ...
    def shutdown_nodes(self, nodes, sig=..., retry=...): ...
    def find(self, name): ...
    def getpids(self, on_down=...): ...
    def __repr__(self): ...
    @property
    def data(self): ...
