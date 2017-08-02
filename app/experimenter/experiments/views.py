from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView

from experimenter.projects.models import Project
from experimenter.experiments.models import Experiment
from experimenter.experiments.serializers import ExperimentSerializer


class ExperimentListView(ListAPIView):
    queryset = Experiment.objects.started()
    serializer_class = ExperimentSerializer
    project_slug_field = 'project__slug'
    filter_fields = (project_slug_field,)

    def get(self, request, *args, **kwargs):
        project_slug = request.query_params.get(
            self.project_slug_field, None)

        if project_slug:
            project_exists = Project.objects.filter(slug=project_slug).exists()

            if not project_exists:
                raise NotFound('A project with that slug does not exist.')

        return super().get(request, *args, **kwargs)
