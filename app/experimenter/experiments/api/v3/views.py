from rest_framework import viewsets

from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v3.serializers import ExperimentRapidSerializer


class ExperimentRapidViewSet(viewsets.ModelViewSet):
    serializer_class = ExperimentRapidSerializer
    queryset = Experiment.objects.filter(type=Experiment.TYPE_RAPID)
    lookup_field = "slug"
