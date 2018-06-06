import django_filters as filters
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, UpdateView
from django_filters.views import FilterView

from experimenter.projects.models import Project
from experimenter.experiments.forms import (
    ExperimentObjectivesForm,
    ExperimentOverviewForm,
    ExperimentRisksForm,
    ExperimentStatusForm,
    ExperimentVariantsForm,
)
from experimenter.experiments.models import Experiment


class ExperimentFiltersetForm(forms.ModelForm):

    class Meta:
        model = Experiment
        fields = (
            "status",
            "firefox_channel",
            "firefox_version",
            "project",
            "owner",
            "archived",
        )

    def clean_archived(self):
        allow_archived = self.cleaned_data.get("archived", False)

        # If we pass in archived=True what we actually mean is
        # don't filter on archived at all, ie show all experiments
        # including archived
        if allow_archived:
            return None

        return False

    def get_project_display_value(self):
        project_id = self.data.get("project", None)

        if project_id is not None:
            return str(Project.objects.get(id=project_id))

    def get_owner_display_value(self):
        user_id = self.data.get("owner", None)

        if user_id is not None:
            return str(get_user_model().objects.get(id=user_id))


class ExperimentFilterset(filters.FilterSet):
    status = filters.ChoiceFilter(
        empty_label="All Statuses",
        choices=Experiment.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    firefox_channel = filters.ChoiceFilter(
        empty_label="All Channels",
        choices=Experiment.CHANNEL_CHOICES[1:],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    firefox_version = filters.ChoiceFilter(
        empty_label="All Versions",
        choices=Experiment.VERSION_CHOICES[1:],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    project = filters.ModelChoiceFilter(
        empty_label="All Projects",
        queryset=Project.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    owner = filters.ModelChoiceFilter(
        empty_label="All Owners",
        queryset=get_user_model().objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    archived = filters.BooleanFilter(
        label="Show archived experiments", widget=forms.CheckboxInput()
    )

    class Meta:
        model = Experiment
        form = ExperimentFiltersetForm
        fields = (
            "status",
            "firefox_channel",
            "firefox_version",
            "owner",
            "project",
            "archived",
        )


class ExperimentOrderingForm(forms.Form):
    ORDERING_CHOICES = (
        ("-latest_change", "Most Recently Updated"),
        ("latest_change", "Least Recently Updated"),
        ("firefox_version", "Firefox Version Ascending"),
        ("-firefox_version", "Firefox Version Descending"),
        ("firefox_channel", "Firefox Channel Ascending"),
        ("-firefox_channel", "Firefox Channel Descending"),
    )

    ordering = forms.ChoiceField(
        choices=ORDERING_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class ExperimentListView(FilterView):
    context_object_name = "experiments"
    filterset_class = ExperimentFilterset
    model = Experiment
    template_name = "experiments/list.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ordering_form = None

    def get_filterset_kwargs(self, *args, **kwargs):
        kwargs = super().get_filterset_kwargs(*args, **kwargs)

        # Always pass in request.GET otherwise the
        # filterset form will be unbound and our custom
        # validation won't kick in
        kwargs["data"] = self.request.GET
        return kwargs

    def get_ordering(self):
        self.ordering_form = ExperimentOrderingForm(self.request.GET)

        if self.ordering_form.is_valid():
            return self.ordering_form.cleaned_data["ordering"]

        return self.ordering_form.ORDERING_CHOICES[0][0]

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            ordering_form=self.ordering_form, *args, **kwargs
        )


class ExperimentFormMixin(object):
    model = Experiment

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        if (
            "action" in self.request.POST
            and self.request.POST["action"] == "continue"
        ):
            return reverse(
                self.next_view_name, kwargs={"slug": self.object.slug}
            )

        return reverse("experiments-detail", kwargs={"slug": self.object.slug})


class ExperimentCreateView(ExperimentFormMixin, CreateView):
    form_class = ExperimentOverviewForm
    next_view_name = "experiments-variants-update"
    template_name = "experiments/edit_overview.html"

    def get_initial(self):
        initial = super().get_initial()

        if "project" in self.request.GET:
            initial["project"] = self.request.GET["project"]

        initial["owner"] = self.request.user.id

        return initial


class ExperimentOverviewUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentOverviewForm
    next_view_name = "experiments-variants-update"
    template_name = "experiments/edit_overview.html"


class ExperimentVariantsUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentVariantsForm
    next_view_name = "experiments-objectives-update"
    template_name = "experiments/edit_variants.html"


class ExperimentObjectivesUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentObjectivesForm
    next_view_name = "experiments-risks-update"
    template_name = "experiments/edit_objectives.html"


class ExperimentRisksUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentRisksForm
    next_view_name = "experiments-detail"
    template_name = "experiments/edit_risks.html"


class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = "experiments/detail.html"


class ExperimentStatusUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentStatusForm
    model = Experiment

    def get_success_url(self):
        return reverse("experiments-detail", kwargs={"slug": self.object.slug})

    def form_invalid(self, form):
        return redirect(
            reverse("experiments-detail", kwargs={"slug": self.object.slug})
        )
