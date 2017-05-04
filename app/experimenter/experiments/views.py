from rest_framework.generics import ListAPIView

from experimenter.experiments.models import Experiment
from experimenter.experiments.serializers import ExperimentSerializer


class ExperimentListView(ListAPIView):
    serializer_class = ExperimentSerializer

    def get_queryset(self):
        project_slug = self.kwargs['project_slug']
        return Experiment.objects.filter(project__slug=project_slug)
