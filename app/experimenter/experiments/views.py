import django_filters as filters
from django import forms
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from django_filters.views import FilterView

from experimenter.experiments.forms import (
    ExperimentStatusForm,
    ExperimentObjectivesForm,
    ExperimentOverviewForm,
    ExperimentRisksForm,
    ExperimentVariantsForm,
)
from experimenter.experiments.models import Experiment


class ExperimentFilter(filters.FilterSet):
    status = filters.ChoiceFilter(
        empty_label='All Statuses',
        choices=Experiment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    firefox_channel = filters.ChoiceFilter(
        empty_label='All Channels',
        choices=Experiment.CHANNEL_CHOICES[1:],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    firefox_version = filters.ChoiceFilter(
        empty_label='All Versions',
        choices=Experiment.VERSION_CHOICES[1:],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Experiment
        fields = (
            'firefox_channel',
            'firefox_version',
            'status',
        )


class ExperimentOrderingForm(forms.Form):
    ORDERING_CHOICES = (
        ('-latest_change', 'Most Recently Updated'),
        ('latest_change', 'Least Recently Updated'),
        ('firefox_version', 'Firefox Version Ascending'),
        ('-firefox_version', 'Firefox Version Descending'),
        ('firefox_channel', 'Firefox Channel Ascending'),
        ('-firefox_channel', 'Firefox Channel Descending'),
    )

    ordering = forms.ChoiceField(
        choices=ORDERING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )


class ExperimentListView(FilterView):
    model = Experiment
    context_object_name = 'experiments'
    template_name = 'experiments/list.html'
    filterset_class = ExperimentFilter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ordering_form = None

    def get_ordering(self):
        self.ordering_form = ExperimentOrderingForm(self.request.GET)

        if self.ordering_form.is_valid():
            return self.ordering_form.cleaned_data['ordering']

        return self.ordering_form.ORDERING_CHOICES[0][0]

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            ordering_form=self.ordering_form, *args, **kwargs)


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


class ExperimentStatusUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentStatusForm
    model = Experiment

    def get_success_url(self):
        return reverse('experiments-detail', kwargs={'slug': self.object.slug})

    def form_invalid(self, form):
        return redirect(
            reverse('experiments-detail', kwargs={'slug': self.object.slug}))
