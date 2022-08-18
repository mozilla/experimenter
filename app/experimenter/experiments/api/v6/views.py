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
