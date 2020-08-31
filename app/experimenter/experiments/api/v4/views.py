from rest_framework import viewsets, mixins

from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer


class ExperimentRapidViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "recipe_slug"
    queryset = (
        Experiment.objects.get_prefetched()
        .filter(type=Experiment.TYPE_RAPID)
        .exclude(status__in=[Experiment.STATUS_DRAFT, Experiment.STATUS_REVIEW])
    )
    serializer_class = ExperimentRapidRecipeSerializer
