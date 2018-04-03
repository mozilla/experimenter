from django.core.urlresolvers import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response

from experimenter.experiments.forms import (
    ExperimentOverviewForm,
    ExperimentVariantsForm,
    ExperimentObjectivesForm,
    ExperimentRisksForm,
)
from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.serializers import (
    ExperimentSerializer,
)


class ExperimentFormMixin(object):
    model = Experiment

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        if (
            'action' in self.request.POST and
            self.request.POST['action'] == 'continue'
        ):
            return reverse(
                self.next_view_name, kwargs={'slug': self.object.slug})

        return reverse('experiments-detail', kwargs={'slug': self.object.slug})


class ExperimentCreateView(ExperimentFormMixin, CreateView):
    form_class = ExperimentOverviewForm
    template_name = 'experiments/edit_overview.html'
    next_view_name = 'experiments-variants-update'

    def get_initial(self):
        initial = super().get_initial()

        if 'project' in self.request.GET:
            initial['project'] = self.request.GET['project']

        return initial


class ExperimentOverviewUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentOverviewForm
    template_name = 'experiments/edit_overview.html'
    next_view_name = 'experiments-variants-update'


class ExperimentVariantsUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentVariantsForm
    template_name = 'experiments/edit_variants.html'
    next_view_name = 'experiments-objectives-update'


class ExperimentObjectivesUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentObjectivesForm
    template_name = 'experiments/edit_objectives.html'
    next_view_name = 'experiments-risks-update'


class ExperimentRisksUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentRisksForm
    template_name = 'experiments/edit_risks.html'
    next_view_name = 'experiments-detail'


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
