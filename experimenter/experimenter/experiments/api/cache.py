import hashlib
import io
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)

DEFAULT_STREAM_CHUNK_SIZE = 25


def get_api_cache_key(view_name, query_params=None):
    if query_params:
        params = sorted(query_params.lists())
        param_str = urlencode(params, doseq=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"nimbus:api:{view_name}:{param_hash}"
    return f"nimbus:api:{view_name}"


def stream_render_queryset(
    queryset,
    serializer_class,
    renderer,
    chunk_size=DEFAULT_STREAM_CHUNK_SIZE,
):
    buf = io.BytesIO()
    buf.write(b"[")
    first = True
    for obj in queryset.iterator(chunk_size=chunk_size):
        item = serializer_class(obj).data
        rendered = renderer.render(item)
        if first:
            first = False
        else:
            buf.write(b",")
        buf.write(rendered)
        del item, rendered
    buf.write(b"]")
    return buf.getvalue()


def warm_api_cache(key_prefix, queryset, serializer_class, renderer=None, sort_key=None):
    if renderer is None:
        renderer = JSONRenderer()

    if sort_key is not None:
        qs = sorted(queryset.all(), key=sort_key, reverse=True)
        data = serializer_class(qs, many=True).data
        rendered = renderer.render(data)
    else:
        rendered = stream_render_queryset(queryset, serializer_class, renderer)

    cache_key = get_api_cache_key(key_prefix)
    cache.set(cache_key, rendered, timeout=settings.API_CACHE_WARMING_TTL)
    logger.info("Warmed cache for %s (%d bytes)", key_prefix, len(rendered))


class CachedListMixin:
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
