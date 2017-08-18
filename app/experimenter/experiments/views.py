from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response

from experimenter.projects.models import Project
from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.serializers import (
    ExperimentSerializer,
)


class ExperimentListView(ListAPIView):
    queryset = Experiment.objects.all()
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


class ExperimentAcceptView(UpdateAPIView):
    queryset = Experiment.objects.filter(status=Experiment.STATUS_PENDING)
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        experiment = self.get_object()

        old_status = experiment.status

        experiment.status = experiment.STATUS_ACCEPTED
        experiment.save()

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=old_status,
            new_status=experiment.status,
            changed_by=self.request.user,
        )

        return Response()


class ExperimentRejectView(UpdateAPIView):
    queryset = Experiment.objects.filter(status=Experiment.STATUS_PENDING)
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        experiment = self.get_object()

        old_status = experiment.status

        experiment.status = experiment.STATUS_REJECTED
        experiment.save()

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=old_status,
            new_status=experiment.status,
            changed_by=self.request.user,
            message=self.request.data.get('message', ''),
        )

        return Response()
