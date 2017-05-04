from django.http import Http404
from rest_framework.generics import ListAPIView

from experimenter.projects.models import Project
from experimenter.experiments.models import Experiment
from experimenter.experiments.serializers import ExperimentSerializer


class ExperimentListView(ListAPIView):
    serializer_class = ExperimentSerializer

    def get_queryset(self):
        project_slug = self.kwargs['project_slug']

        if not Project.objects.filter(slug=project_slug).exists():
            raise Http404

        return Experiment.objects.filter(
            project__slug=project_slug).filter(active=True)
