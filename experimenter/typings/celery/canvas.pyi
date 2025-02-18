"""
This type stub file was generated by pyright.
"""

from celery.utils import abstract
from kombu.utils.objects import cached_property

"""Composing task work-flows.

.. seealso:

    You should import these from :mod:`celery` and not this module.
"""
__all__ = (
    "Signature",
    "chain",
    "xmap",
    "xstarmap",
    "chunks",
    "group",
    "chord",
    "signature",
    "maybe_signature",
)

def maybe_unroll_group(group):
    """Unroll group with only one member."""
    ...

def task_name_from(task): ...
@abstract.CallableSignature.register
class Signature(dict):
    """Task Signature.

    Class that wraps the arguments and execution options
    for a single task invocation.

    Used as the parts in a :class:`group` and other constructs,
    or to pass tasks around as callbacks while being compatible
    with serializers with a strict type subset.

    Signatures can also be created from tasks:

    - Using the ``.signature()`` method that has the same signature
      as ``Task.apply_async``:

        .. code-block:: pycon

            >>> add.signature(args=(1,), kwargs={"kw": 2}, options={})

    - or the ``.s()`` shortcut that works for star arguments:

        .. code-block:: pycon

            >>> add.s(1, kw=2)

    - the ``.s()`` shortcut does not allow you to specify execution options
      but there's a chaning `.set` method that returns the signature:

        .. code-block:: pycon

            >>> add.s(2, 2).set(countdown=10).set(expires=30).delay()

    Note:
        You should use :func:`~celery.signature` to create new signatures.
        The ``Signature`` class is the type returned by that function and
        should be used for ``isinstance`` checks for signatures.

    See Also:
        :ref:`guide-canvas` for the complete guide.

    Arguments:
        task (Union[Type[celery.app.task.Task], str]): Either a task
            class/instance, or the name of a task.
        args (Tuple): Positional arguments to apply.
        kwargs (Dict): Keyword arguments to apply.
        options (Dict): Additional options to :meth:`Task.apply_async`.

    Note:
        If the first argument is a :class:`dict`, the other
        arguments will be ignored and the values in the dict will be used
        instead::

            >>> s = signature('tasks.add', args=(2, 2))
            >>> signature(s)
            {'task': 'tasks.add', args=(2, 2), kwargs={}, options={}}
    """

    TYPES = ...
    _app = ...
    _IMMUTABLE_OPTIONS = ...
    @classmethod
    def register_type(cls, name=...): ...
    @classmethod
    def from_dict(cls, d, app=...): ...
    def __init__(
        self,
        task=...,
        args=...,
        kwargs=...,
        options=...,
        type=...,
        subtask_type=...,
        immutable=...,
        app=...,
        **ex,
    ) -> None: ...
    def __call__(self, *partial_args, **partial_kwargs):
        """Call the task directly (in the current process)."""
        ...
    def delay(self, *partial_args, **partial_kwargs):  # -> None:
        """Shortcut to :meth:`apply_async` using star arguments."""
        ...
    def apply(self, args=..., kwargs=..., **options):
        """Call task locally.

        Same as :meth:`apply_async` but executed the task inline instead
        of sending a task message.
        """
        ...
    def apply_async(self, args=..., kwargs=..., route_name=..., **options):  # -> None:
        """Apply this task asynchronously.

        Arguments:
            args (Tuple): Partial args to be prepended to the existing args.
            kwargs (Dict): Partial kwargs to be merged with existing kwargs.
            options (Dict): Partial options to be merged
                with existing options.

        Returns:
            ~@AsyncResult: promise of future evaluation.

        See also:
            :meth:`~@Task.apply_async` and the :ref:`guide-calling` guide.
        """
        ...
    def clone(self, args=..., kwargs=..., **opts):  # -> Signature:
        """Create a copy of this signature.

        Arguments:
            args (Tuple): Partial args to be prepended to the existing args.
            kwargs (Dict): Partial kwargs to be merged with existing kwargs.
            options (Dict): Partial options to be merged with
                existing options.
        """
        ...
    partial = ...
    def freeze(
        self,
        _id=...,
        group_id=...,
        chord=...,
        root_id=...,
        parent_id=...,
        group_index=...,
    ):
        """Finalize the signature by adding a concrete task id.

        The task won't be called and you shouldn't call the signature
        twice after freezing it as that'll result in two task messages
        using the same task id.

        Returns:
            ~@AsyncResult: promise of future evaluation.
        """
        ...
    _freeze = ...
    def replace(self, args=..., kwargs=..., options=...):  # -> Signature:
        """Replace the args, kwargs or options set for this signature.

        These are only replaced if the argument for the section is
        not :const:`None`.
        """
        ...
    def set(self, immutable=..., **options):  # -> Self@Signature:
        """Set arbitrary execution options (same as ``.options.update(…)``).

        Returns:
            Signature: This is a chaining method call
                (i.e., it will return ``self``).
        """
        ...
    def set_immutable(self, immutable): ...
    def append_to_list_option(self, key, value): ...
    def extend_list_option(self, key, value): ...
    def link(self, callback):
        """Add callback task to be applied if this task succeeds.

        Returns:
            Signature: the argument passed, for chaining
                or use with :func:`~functools.reduce`.
        """
        ...
    def link_error(self, errback):
        """Add callback task to be applied on error in task execution.

        Returns:
            Signature: the argument passed, for chaining
                or use with :func:`~functools.reduce`.
        """
        ...
    def on_error(self, errback):  # -> Self@Signature:
        """Version of :meth:`link_error` that supports chaining.

        on_error chains the original signature, not the errback so::

            >>> add.s(2, 2).on_error(errback.s()).delay()

        calls the ``add`` task, not the ``errback`` task, but the
        reverse is true for :meth:`link_error`.
        """
        ...
    def flatten_links(self):  # -> list[Any]:
        """Return a recursive list of dependencies.

        "unchain" if you will, but with links intact.
        """
        ...
    def __or__(self, other): ...
    def __ior__(self, other): ...
    def election(self): ...
    def reprcall(self, *args, **kwargs): ...
    def __deepcopy__(self, memo): ...
    def __invert__(self): ...
    def __reduce__(self): ...
    def __json__(self): ...
    def __repr__(self): ...
    def items(self): ...
    @property
    def name(self): ...
    @cached_property
    def type(self): ...
    @cached_property
    def app(self): ...
    @cached_property
    def AsyncResult(self): ...
    id = ...
    parent_id = ...
    root_id = ...
    task = ...
    args = ...
    kwargs = ...
    options = ...
    subtask_type = ...
    immutable = ...

@Signature.register_type(name="chain")
class _chain(Signature):
    tasks = ...
    @classmethod
    def from_dict(cls, d, app=...): ...
    def __init__(self, *tasks, **options) -> None: ...
    def __call__(self, *args, **kwargs): ...
    def clone(self, *args, **kwargs): ...
    def unchain_tasks(self): ...
    def apply_async(self, args=..., kwargs=..., **options): ...
    def run(
        self,
        args=...,
        kwargs=...,
        group_id=...,
        chord=...,
        task_id=...,
        link=...,
        link_error=...,
        publisher=...,
        producer=...,
        root_id=...,
        parent_id=...,
        app=...,
        group_index=...,
        **options,
    ): ...
    def freeze(
        self,
        _id=...,
        group_id=...,
        chord=...,
        root_id=...,
        parent_id=...,
        group_index=...,
    ): ...
    def prepare_steps(
        self,
        args,
        kwargs,
        tasks,
        root_id=...,
        parent_id=...,
        link_error=...,
        app=...,
        last_task_id=...,
        group_id=...,
        chord_body=...,
        clone=...,
        from_dict=...,
        group_index=...,
    ): ...
    def apply(self, args=..., kwargs=..., **options): ...
    @property
    def app(self): ...
    def __repr__(self): ...

class chain(_chain):
    """Chain tasks together.

    Each tasks follows one another,
    by being applied as a callback of the previous task.

    Note:
        If called with only one argument, then that argument must
        be an iterable of tasks to chain: this allows us
        to use generator expressions.

    Example:
        This is effectively :math:`((2 + 2) + 4)`:

        .. code-block:: pycon

            >>> res = chain(add.s(2, 2), add.s(4))()
            >>> res.get()
            8

        Calling a chain will return the result of the last task in the chain.
        You can get to the other tasks by following the ``result.parent``'s:

        .. code-block:: pycon

            >>> res.parent.get()
            4

        Using a generator expression:

        .. code-block:: pycon

            >>> lazy_chain = chain(add.s(i) for i in range(10))
            >>> res = lazy_chain(3)

    Arguments:
        *tasks (Signature): List of task signatures to chain.
            If only one argument is passed and that argument is
            an iterable, then that'll be used as the list of signatures
            to chain instead.  This means that you can use a generator
            expression.

    Returns:
        ~celery.chain: A lazy signature that can be called to apply the first
            task in the chain.  When that task succeeds the next task in the
            chain is applied, and so on.
    """

    def __new__(cls, *tasks, **kwargs): ...

class _basemap(Signature):
    _task_name = ...
    _unpack_args = ...
    @classmethod
    def from_dict(cls, d, app=...): ...
    def __init__(self, task, it, **options) -> None: ...
    def apply_async(self, args=..., kwargs=..., **opts): ...

@Signature.register_type()
class xmap(_basemap):
    """Map operation for tasks.

    Note:
        Tasks executed sequentially in process, this is not a
        parallel operation like :class:`group`.
    """

    _task_name = ...
    def __repr__(self): ...

@Signature.register_type()
class xstarmap(_basemap):
    """Map operation for tasks, using star arguments."""

    _task_name = ...
    def __repr__(self): ...

@Signature.register_type()
class chunks(Signature):
    """Partition of tasks into chunks of size n."""

    _unpack_args = ...
    @classmethod
    def from_dict(cls, d, app=...): ...
    def __init__(self, task, it, n, **options) -> None: ...
    def __call__(self, **options): ...
    def apply_async(self, args=..., kwargs=..., **opts): ...
    def group(self): ...
    @classmethod
    def apply_chunks(cls, task, it, n, app=...): ...

@Signature.register_type()
class group(Signature):
    """Creates a group of tasks to be executed in parallel.

    A group is lazy so you must call it to take action and evaluate
    the group.

    Note:
        If only one argument is passed, and that argument is an iterable
        then that'll be used as the list of tasks instead: this
        allows us to use ``group`` with generator expressions.

    Example:
        >>> lazy_group = group([add.s(2, 2), add.s(4, 4)])
        >>> promise = lazy_group()  # <-- evaluate: returns lazy result.
        >>> promise.get()  # <-- will wait for the task to return
        [4, 8]

    Arguments:
        *tasks (List[Signature]): A list of signatures that this group will
            call. If there's only one argument, and that argument is an
            iterable, then that'll define the list of signatures instead.
        **options (Any): Execution options applied to all tasks
            in the group.

    Returns:
        ~celery.group: signature that when called will then call all of the
            tasks in the group (and return a :class:`GroupResult` instance
            that can be used to inspect the state of the group).
    """

    tasks = ...
    @classmethod
    def from_dict(cls, d, app=...): ...
    def __init__(self, *tasks, **options) -> None: ...
    def __call__(self, *partial_args, **options): ...
    def skew(self, start=..., stop=..., step=...): ...
    def apply_async(
        self,
        args=...,
        kwargs=...,
        add_to_parent=...,
        producer=...,
        link=...,
        link_error=...,
        **options,
    ): ...
    def apply(self, args=..., kwargs=..., **options): ...
    def set_immutable(self, immutable): ...
    def link(self, sig): ...
    def link_error(self, sig): ...
    def freeze(
        self,
        _id=...,
        group_id=...,
        chord=...,
        root_id=...,
        parent_id=...,
        group_index=...,
    ): ...
    _freeze = ...
    def __repr__(self): ...
    def __len__(self): ...
    @property
    def app(self): ...

@Signature.register_type(name="chord")
class _chord(Signature):
    r"""Barrier synchronization primitive.

    A chord consists of a header and a body.

    The header is a group of tasks that must complete before the callback is
    called.  A chord is essentially a callback for a group of tasks.

    The body is applied with the return values of all the header
    tasks as a list.

    Example:

        The chord:

        .. code-block:: pycon

            >>> res = chord([add.s(2, 2), add.s(4, 4)])(sum_task.s())

        is effectively :math:`\Sigma ((2 + 2) + (4 + 4))`:

        .. code-block:: pycon

            >>> res.get()
            12
    """
    @classmethod
    def from_dict(cls, d, app=...): ...
    def __init__(
        self, header, body=..., task=..., args=..., kwargs=..., app=..., **options
    ) -> None: ...
    def __call__(self, body=..., **options): ...
    def freeze(
        self,
        _id=...,
        group_id=...,
        chord=...,
        root_id=...,
        parent_id=...,
        group_index=...,
    ): ...
    def apply_async(
        self,
        args=...,
        kwargs=...,
        task_id=...,
        producer=...,
        publisher=...,
        connection=...,
        router=...,
        result_cls=...,
        **options,
    ): ...
    def apply(self, args=..., kwargs=..., propagate=..., body=..., **options): ...
    def __length_hint__(self): ...
    def run(
        self,
        header,
        body,
        partial_args,
        app=...,
        interval=...,
        countdown=...,
        max_retries=...,
        eager=...,
        task_id=...,
        **options,
    ): ...
    def clone(self, *args, **kwargs): ...
    def link(self, callback): ...
    def link_error(self, errback): ...
    def set_immutable(self, immutable): ...
    def __repr__(self): ...
    @cached_property
    def app(self): ...
    tasks = ...
    body = ...

chord = _chord

def signature(varies, *args, **kwargs):  # -> Signature | None:
    """Create new signature.

    - if the first argument is a signature already then it's cloned.
    - if the first argument is a dict, then a Signature version is returned.

    Returns:
        Signature: The resulting signature.
    """
    ...

subtask = ...

def maybe_signature(d, app=..., clone=...):  # -> CallableSignature | Signature | None:
    """Ensure obj is a signature, or None.

    Arguments:
        d (Optional[Union[abstract.CallableSignature, Mapping]]):
            Signature or dict-serialized signature.
        app (celery.Celery):
            App to bind signature to.
        clone (bool):
            If d' is already a signature, the signature
           will be cloned when this flag is enabled.

    Returns:
        Optional[abstract.CallableSignature]
    """
    ...

maybe_subtask = ...
