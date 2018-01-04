from django.views.generic import DetailView
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response

from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.serializers import (
    ExperimentSerializer,
)


class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = 'experiments/detail.html'


class ExperimentListView(ListAPIView):
    filter_fields = ('project__slug', 'status')
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer


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
