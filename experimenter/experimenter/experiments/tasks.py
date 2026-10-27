import markus
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.experiments.api.cache import warm_api_cache
from experimenter.experiments.constants import NimbusConstants

logger = get_task_logger(__name__)
metrics = markus.get_metrics("experiments.api_cache")


def _start_date_sort_key(experiment):
    return (experiment.start_date and experiment.start_date.strftime("%Y-%m-%d")) or ""


class WarmCacheEndpoint:
    def __init__(
        self,
        key_prefix,
        queryset,
        serializer_class,
        params="",
        filterset_class=None,
        kwargs=None,
    ):
        self.key_prefix = key_prefix
        self.queryset = queryset
        self.serializer_class = serializer_class
        self.params = params
        self.filterset_class = filterset_class
        self.kwargs = kwargs or {}

    @property
    def name(self):
        if self.params:
            return f"{self.key_prefix}?{self.params}"
        return self.key_prefix


def _get_warm_cache_endpoints():
    """Return the list of endpoints to warm.

    Imports are deferred so the module can be loaded before Django is fully
    initialised (Celery auto-discovery).
    """
    from experimenter.experiments.api.v5 import serializers as v5_ser
    from experimenter.experiments.api.v5 import views as v5_views
    from experimenter.experiments.api.v6 import serializers as v6_ser
    from experimenter.experiments.api.v6 import views as v6_views
    from experimenter.experiments.api.v7 import serializers as v7_ser
    from experimenter.experiments.api.v7 import views as v7_views
    from experimenter.experiments.api.v8 import serializers as v8_ser
    from experimenter.experiments.api.v8 import views as v8_views

    desktop = NimbusConstants.Application.DESKTOP
    complete = NimbusConstants.Status.COMPLETE

    return [
        WarmCacheEndpoint(
            "v5:csv",
            v5_views.NimbusExperimentCsvListView.queryset,
            v5_ser.NimbusExperimentCsvSerializer,
            kwargs={
                "renderer": v5_views.NimbusExperimentCsvRenderer(),
                "sort_key": _start_date_sort_key,
            },
        ),
        WarmCacheEndpoint(
            "v6:experiments",
            v6_views.NimbusExperimentViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
        ),
        WarmCacheEndpoint(
            "v6:experiments",
            v6_views.NimbusExperimentViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
            params=f"status={complete}",
            filterset_class=v6_views.NimbusExperimentViewSet.filterset_class,
        ),
        WarmCacheEndpoint(
            "v6:experiments",
            v6_views.NimbusExperimentViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
            params=f"application={desktop}",
            filterset_class=v6_views.NimbusExperimentViewSet.filterset_class,
        ),
        WarmCacheEndpoint(
            "v6:experiments",
            v6_views.NimbusExperimentViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
            params="is_first_run=false",
            filterset_class=v6_views.NimbusExperimentViewSet.filterset_class,
        ),
        WarmCacheEndpoint(
            "v6:draft-experiments",
            v6_views.NimbusExperimentDraftViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
        ),
        WarmCacheEndpoint(
            "v7:experiments",
            v7_views.NimbusExperimentViewSet.queryset,
            v7_ser.NimbusExperimentSerializer,
        ),
        WarmCacheEndpoint(
            "v7:experiments",
            v7_views.NimbusExperimentViewSet.queryset,
            v7_ser.NimbusExperimentSerializer,
            params=f"application={desktop}&status={complete}",
            filterset_class=v7_views.NimbusExperimentViewSet.filterset_class,
        ),
        WarmCacheEndpoint(
            "v8:experiments",
            v8_views.NimbusExperimentViewSet.queryset,
            v8_ser.NimbusExperimentSerializer,
        ),
        WarmCacheEndpoint(
            "v8:experiments",
            v8_views.NimbusExperimentViewSet.queryset,
            v8_ser.NimbusExperimentSerializer,
            params=f"application={desktop}",
            filterset_class=v8_views.NimbusExperimentViewSet.filterset_class,
        ),
        WarmCacheEndpoint(
            "v8:draft-experiments",
            v8_views.NimbusExperimentDraftViewSet.queryset,
            v8_ser.NimbusExperimentSerializer,
        ),
    ]


def _get_warm_cache_endpoint(name):
    for endpoint in _get_warm_cache_endpoints():
        if endpoint.name == name:
            return endpoint
    return None


@app.task
@metrics.timer_decorator("warm_api_cache_endpoint")
def warm_api_cache_endpoint(name):
    metrics.incr(f"warm_api_cache_endpoint.{name}.started")
    endpoint = _get_warm_cache_endpoint(name)
    if endpoint is None:
        metrics.incr(f"warm_api_cache_endpoint.{name}.unknown")
        logger.error("Unknown cache endpoint: %s", name)
        return

    try:
        warm_api_cache(
            endpoint.key_prefix,
            endpoint.queryset,
            endpoint.serializer_class,
            filterset_class=endpoint.filterset_class,
            params=endpoint.params,
            **endpoint.kwargs,
        )
        logger.info("Warmed %s", name)
        metrics.incr(f"warm_api_cache_endpoint.{name}.completed")
    except Exception as e:
        metrics.incr(f"warm_api_cache_endpoint.{name}.failed")
        logger.exception("Failed to warm %s: %s", name, e)
        raise


@app.task
def warm_api_caches():
    metrics.incr("warm_api_caches.dispatched")
    for endpoint in _get_warm_cache_endpoints():
        warm_api_cache_endpoint.delay(endpoint.name)
