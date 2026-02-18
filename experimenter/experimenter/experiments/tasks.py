import markus
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.experiments.api.cache import warm_api_cache

logger = get_task_logger(__name__)
metrics = markus.get_metrics("experiments.api_cache")


def _get_warm_cache_endpoints():
    """Return the list of (key_prefix, queryset, serializer_class) to warm.

    Imports are deferred so the module can be loaded before Django is fully
    initialised (Celery auto-discovery).
    """
    from experimenter.experiments.api.v6 import serializers as v6_ser
    from experimenter.experiments.api.v6 import views as v6_views
    from experimenter.experiments.api.v7 import serializers as v7_ser
    from experimenter.experiments.api.v7 import views as v7_views
    from experimenter.experiments.api.v8 import serializers as v8_ser
    from experimenter.experiments.api.v8 import views as v8_views

    return [
        (
            "v6:experiments",
            v6_views.NimbusExperimentViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
        ),
        (
            "v6:draft-experiments",
            v6_views.NimbusExperimentDraftViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
        ),
        (
            "v6:first-run",
            v6_views.NimbusExperimentFirstRunViewSet.queryset,
            v6_ser.NimbusExperimentSerializer,
        ),
        (
            "v7:experiments",
            v7_views.NimbusExperimentViewSet.queryset,
            v7_ser.NimbusExperimentSerializer,
        ),
        (
            "v8:experiments",
            v8_views.NimbusExperimentViewSet.queryset,
            v8_ser.NimbusExperimentSerializer,
        ),
        (
            "v8:draft-experiments",
            v8_views.NimbusExperimentDraftViewSet.queryset,
            v8_ser.NimbusExperimentSerializer,
        ),
    ]


@app.task
@metrics.timer_decorator("warm_api_caches")
def warm_api_caches():
    """Pre-populate the API list cache so requests are always served instantly."""
    metrics.incr("warm_api_caches.started")

    try:
        for key_prefix, queryset, serializer_class in _get_warm_cache_endpoints():
            warm_api_cache(key_prefix, queryset, serializer_class)
            logger.info("Warmed %s", key_prefix)

        metrics.incr("warm_api_caches.completed")

    except Exception as e:
        metrics.incr("warm_api_caches.failed")
        logger.exception("warm_api_caches failed: %s", e)
        raise
