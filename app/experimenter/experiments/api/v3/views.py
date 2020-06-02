from rest_framework import viewsets, exceptions

from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v3.serializers import ExperimentRapidSerializer


class ExperimentRapidViewSet(viewsets.ModelViewSet):
    serializer_class = ExperimentRapidSerializer
    queryset = Experiment.objects.filter(type=Experiment.TYPE_RAPID)
    lookup_field = "slug"

    def list(self, request):
        raise exceptions.MethodNotAllowed(request.method)
