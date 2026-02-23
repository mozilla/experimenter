import hashlib
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)


def get_api_cache_key(view_name, query_params=None):
    """Build a deterministic cache key from the view name and query parameters."""
    if query_params:
        params = sorted(query_params.lists())
        param_str = urlencode(params, doseq=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"nimbus:api:{view_name}:{param_hash}"
    return f"nimbus:api:{view_name}"


def warm_api_cache(key_prefix, queryset, serializer_class, renderer=None, sort_key=None):
    """Query the DB, serialize, and store the rendered response in the cache."""
    if renderer is None:
        renderer = JSONRenderer()
    qs = queryset.all()
    if sort_key is not None:
        qs = sorted(qs, key=sort_key, reverse=True)
    data = serializer_class(qs, many=True).data
    rendered = renderer.render(data)
    if isinstance(rendered, str):
        rendered = rendered.encode("utf-8")
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
