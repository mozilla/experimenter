from rest_framework import viewsets, mixins

from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer


class ExperimentRapidViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
):
    lookup_field = "slug"
    queryset = (
        Experiment.objects.get_prefetched()
        .filter(type=Experiment.TYPE_RAPID)
        .exclude(status=Experiment.STATUS_DRAFT)
    )
    serializer_class = ExperimentRapidRecipeSerializer
