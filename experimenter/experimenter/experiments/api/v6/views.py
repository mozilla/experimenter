from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment


class NimbusExperimentViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "slug"
    queryset = (
        NimbusExperiment.objects.with_related()
        .exclude(status__in=[NimbusExperiment.Status.DRAFT])
        .order_by("slug")
    )
    serializer_class = NimbusExperimentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_first_run"]

    @method_decorator(cache_page(settings.V6_API_CACHE_DURATION))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class NimbusExperimentDraftViewSet(NimbusExperimentViewSet):
    queryset = (
        NimbusExperiment.objects.with_related()
        .filter(status=NimbusExperiment.Status.DRAFT)
        .order_by("slug")
    )
    filterset_fields = ["is_localized"]


class NimbusExperimentFirstRunViewSet(NimbusExperimentViewSet):
    queryset = (
        NimbusExperiment.objects.with_related()
        .filter(status=NimbusExperiment.Status.LIVE)
        .filter(is_first_run=True)
        .order_by("slug")
    )
