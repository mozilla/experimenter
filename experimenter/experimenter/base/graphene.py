import traceback  # pragma: no cover


class GrapheneExceptionMiddleware:  # pragma: no cover
    """Print exceptions to the console instead of swallowing them.

    The default behaviour for graphene-django when an exception occurs is to
    produce an error page with the exception message. This middleware will also
    log the traceback from the exception to the console to aid in debugging.
    """

    def resolve(self, next_middleware, root, info, **kwargs):
        try:
            return next_middleware(root, info, **kwargs)
        except Exception:
            traceback.print_exc()
            raise
