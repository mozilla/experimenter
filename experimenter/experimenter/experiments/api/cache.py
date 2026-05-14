import hashlib
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.compat import SHORT_SEPARATORS
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder as DRFJSONEncoder

logger = logging.getLogger(__name__)

DEFAULT_STREAM_CHUNK_SIZE = 25


def get_api_cache_key(view_name, query_params=None):
    """Build a deterministic cache key from the view name and query parameters."""
    if query_params:
        params = sorted(query_params.lists())
        param_str = urlencode(params, doseq=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"nimbus:api:{view_name}:{param_hash}"
    return f"nimbus:api:{view_name}"


class _StreamArray(list[object]):
    """Lets ``stream_render_queryset`` actually stream the queryset, rather than
    holding the whole serialised graph in memory.
    """

    def __init__(self, gen):
        super().__init__()
        self._iter = iter(gen)
        try:
            self._first = next(self._iter)
            self._empty = False
        except StopIteration:
            self._empty = True

    def __iter__(self):
        yield self._first
        yield from self._iter

    def __len__(self):
        return 0 if self._empty else 1


def _drf_compatible_encoder():
    """Keeps the warm cache and a fresh on-miss render byte-identical for the
    same data.
    """
    return DRFJSONEncoder(
        ensure_ascii=JSONRenderer.ensure_ascii,
        allow_nan=not JSONRenderer.strict,
        separators=SHORT_SEPARATORS,
    )


def stream_render_queryset(
    queryset,
    serializer_class,
    chunk_size=DEFAULT_STREAM_CHUNK_SIZE,
):
    """Streams the warm-cache JSON in bounded memory — materialising it all at
    once OOM-kills the worker (#15621).
    """
    items = (
        serializer_class(obj).data for obj in queryset.iterator(chunk_size=chunk_size)
    )
    encoder = _drf_compatible_encoder()
    return b"".join(
        chunk.encode("utf-8") for chunk in encoder.iterencode(_StreamArray(items))
    )


def warm_api_cache(key_prefix, queryset, serializer_class, renderer=None, sort_key=None):
    """Query the DB, serialize, and store the rendered response in the cache."""
    if renderer is None:
        renderer = JSONRenderer()

    if sort_key is not None:
        qs = sorted(queryset.all(), key=sort_key, reverse=True)
        data = serializer_class(qs, many=True).data
        rendered = renderer.render(data)
    else:
        rendered = stream_render_queryset(queryset, serializer_class)

    cache_key = get_api_cache_key(key_prefix)
    cache.set(cache_key, rendered, timeout=settings.API_CACHE_WARMING_TTL)
    logger.info("Warmed cache for %s (%d bytes)", key_prefix, len(rendered))


class CachedListMixin:
    """Mixin that serves list responses from an application-level Redis cache.

    Set ``cache_key_prefix`` on each viewset (e.g. "v6:experiments").
    The Celery task ``warm_api_caches`` pre-populates the cache for unfiltered
    requests.  Filtered requests are cached on first hit.
    """

    cache_key_prefix = ""
    cache_content_type = "application/json"

    def list(self, request, *args, **kwargs):
        cache_key = get_api_cache_key(self.cache_key_prefix, request.query_params)
        cached = cache.get(cache_key)
        if cached is not None:
            return HttpResponse(cached, content_type=self.cache_content_type)

        response = super().list(request, *args, **kwargs)
        renderer = self.renderer_classes[0]()
        rendered = renderer.render(response.data)
        if isinstance(rendered, str):
            rendered = rendered.encode("utf-8")
        cache.set(cache_key, rendered, timeout=settings.API_CACHE_WARMING_TTL)
        return response
