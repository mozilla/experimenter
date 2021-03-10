from rest_framework import mixins, viewsets

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment


class NimbusExperimentViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "slug"
    queryset = NimbusExperiment.objects.all().exclude(
        status__in=[NimbusExperiment.Status.DRAFT]
    )
    serializer_class = NimbusExperimentSerializer
