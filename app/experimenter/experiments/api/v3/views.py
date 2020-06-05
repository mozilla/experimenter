from rest_framework import viewsets, mixins

from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v3.serializers import ExperimentRapidSerializer


class ExperimentRapidViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ExperimentRapidSerializer
    queryset = Experiment.objects.filter(type=Experiment.TYPE_RAPID)
    lookup_field = "slug"
