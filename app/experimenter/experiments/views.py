import django_filters as filters
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, F, IntegerField
from django.db.models.functions import Cast
from django.db.models.expressions import Func, Value
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.edit import ModelFormMixin
from django_filters.views import FilterView
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
)
import django_filters.widgets as widgets

from experimenter.projects.models import Project
from experimenter.experiments.forms import (
    ExperimentArchiveForm,
    ExperimentCommentForm,
    ExperimentObjectivesForm,
    ExperimentOverviewForm,
    ExperimentReviewForm,
    ExperimentRisksForm,
    ExperimentStatusForm,
    ExperimentSubscribedForm,
    ExperimentVariantsAddonForm,
    ExperimentVariantsPrefForm,
    NormandyIdForm,
)
from experimenter.experiments.models import Experiment


class ExperimentFiltersetForm(forms.ModelForm):
    in_qa = forms.BooleanField(required=False)
    surveys = forms.BooleanField(required=False)
    search = forms.CharField(required=False)
    subscribed = forms.BooleanField(required=False)
    firefox_version = forms.CharField(required=False)
    longrunning = forms.BooleanField(required=False)

    class Meta:
        model = Experiment
        fields = (
            "search",
            "type",
            "status",
            "firefox_channel",
            "firefox_version",
            "project",
            "owner",
            "in_qa",
            "surveys",
            "archived",
            "subscribed",
            "longrunning",
        )

    def clean_archived(self):
        allow_archived = self.cleaned_data.get("archived", False)

        # If we pass in archived=True what we actually mean is
        # don't filter on archived at all, ie show all experiments
        # including archived
        if allow_archived:
            return None

        return False

    def get_type_display_value(self):
        return dict(Experiment.TYPE_CHOICES).get(self.data.get("type"))

    def get_project_display_value(self):
        project_id = self.data.get("project", None)

        if project_id is not None:
            return str(Project.objects.get(id=project_id))

    def get_owner_display_value(self):
        user_id = self.data.get("owner", None)

        if user_id is not None:
            return str(get_user_model().objects.get(id=user_id))

    def get_display_start_date_info(self):
        experiment_date_field = self.data.get("experiment_date_field")
        date_after = self.data.get("date_range_after")
        date_before = self.data.get("date_range_before")

        if date_after and date_before:
            return (
                f"{experiment_date_field} between "
                f"{date_after} and {date_before}"
            )
        elif date_after and date_before == "":
            return f"{experiment_date_field} after {date_after}"
        elif date_after == "" and date_before:
            return f"{experiment_date_field} before {date_before}"
        else:
            return ""


# the default widget has a dash character between the two date fields,
# and what we want is the word "To", so we are making our own widget here
class DateRangeWidget(widgets.DateRangeWidget):
    template_name = "widgets/date_range.html"


class SearchWidget(forms.widgets.TextInput):
    template_name = "widgets/search.html"


class ExperimentFilterset(filters.FilterSet):

    search = filters.CharFilter(
        method="filter_search",
        widget=SearchWidget(
            attrs={
                "class": "form-control",
                "placeholder": "Search Experiments",
            }
        ),
    )
    type = filters.ChoiceFilter(
        empty_label="All Types",
        choices=Experiment.TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
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
        method="version_filter",
    )
    project = filters.ModelChoiceFilter(
        empty_label="All Projects",
        queryset=Project.objects.all().order_by("name"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    owner = filters.ModelChoiceFilter(
        empty_label="All Owners",
        queryset=get_user_model().objects.all().order_by("email"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    archived = filters.BooleanFilter(
        label="Show archived experiments", widget=forms.CheckboxInput()
    )
    experiment_date_field = filters.ChoiceFilter(
        empty_label="No Date Restriction",
        choices=[
            (Experiment.EXPERIMENT_STARTS, "Experiment Starts"),
            (Experiment.EXPERIMENT_PAUSES, "Experiment Pauses"),
            (Experiment.EXPERIMENT_ENDS, "Experiment Ends"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
        method="experiment_date_field_filter",
    )
    date_range = filters.DateFromToRangeFilter(
        method="date_range_filter",
        widget=DateRangeWidget(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    in_qa = filters.BooleanFilter(
        label="Show only experiments in QA",
        widget=forms.CheckboxInput(),
        method="in_qa_filter",
    )

    surveys = filters.BooleanFilter(
        label="Show experiments with surveys",
        widget=forms.CheckboxInput(),
        method="surveys_filter",
    )

    subscribed = filters.BooleanFilter(
        label="Show subscribed experiments",
        widget=forms.CheckboxInput(),
        method="subscribed_filter",
    )

    longrunning = filters.BooleanFilter(
        label="Show long-running experiments",
        widget=forms.CheckboxInput(),
        method="longrunning_filter",
    )

    class Meta:
        model = Experiment
        form = ExperimentFiltersetForm
        fields = ExperimentFiltersetForm.Meta.fields

    def filter_search(self, queryset, name, value):
        vector = SearchVector(
            "name",
            "short_description",
            "owner__email",
            "slug",
            "related_work",
            "addon_experiment_id",
            "pref_key",
            "public_name",
            "public_description",
            "objectives",
            "analysis",
            "analysis_owner",
            "engineering_owner",
            "bugzilla_id",
            "normandy_slug",
        )

        query = SearchQuery(value)

        return (
            queryset.annotate(rank=SearchRank(vector, query), search=vector)
            .filter(search=value)
            .order_by("-rank")
        )

    def experiment_date_field_filter(self, queryset, name, value):
        # this custom method isn't doing anything. There has to
        # be a custom method to be able to display the select
        # filter that controls which date range we show
        return queryset

    def version_filter(self, queryset, name, value):

        return queryset.filter(
            Q(firefox_min_version__lte=value, firefox_max_version__gte=value)
            | Q(firefox_min_version=value)
        )

    def date_range_filter(self, queryset, name, value):

        date_type = self.form.cleaned_data["experiment_date_field"]

        experiment_date_field = {
            Experiment.EXPERIMENT_STARTS: "start_date",
            Experiment.EXPERIMENT_PAUSES: "enrollment_end_date",
            Experiment.EXPERIMENT_ENDS: "end_date",
        }[date_type]

        results = []

        for experiment in queryset.all():
            date = getattr(experiment, experiment_date_field)

            # enrollment end dates are optional, so there won't always
            # be a pause date for an experiment
            if date:
                if value.start and date < value.start.date():
                    continue
                if value.stop and date > value.stop.date():
                    continue
                results.append(experiment.id)

        return queryset.filter(pk__in=results)

    def in_qa_filter(self, queryset, name, value):
        if value:
            return queryset.filter(review_qa_requested=True, review_qa=False)

        return queryset

    def surveys_filter(self, queryset, name, value):
        if value:
            return queryset.filter(survey_required=True)

        return queryset

    def subscribed_filter(self, queryset, name, value):
        if value:
            return queryset.filter(subscribers__in=[self.request.user.id])

        return queryset

    def longrunning_filter(self, queryset, name, value):
        if value:
            return (
                queryset.exclude(firefox_max_version__exact="")
                .annotate(
                    firefox_min_int=Cast(
                        Func(
                            F("firefox_min_version"),
                            Value(r"[\d]+"),
                            function="substring",
                        ),
                        IntegerField(),
                    ),
                    firefox_max_int=Cast(
                        Func(
                            F("firefox_max_version"),
                            Value(r"[\d]+"),
                            function="substring",
                        ),
                        IntegerField(),
                    ),
                    version_count=F("firefox_max_int") - F("firefox_min_int"),
                )
                .filter(version_count__gte=3)
            )

        return queryset


class ExperimentOrderingForm(forms.Form):
    ORDERING_CHOICES = (
        ("-latest_change", "Most Recently Updated"),
        ("latest_change", "Least Recently Updated"),
        ("firefox_min_version", "Firefox Min Version Ascending"),
        ("-firefox_min_version", "Firefox Min Version Descending"),
        ("firefox_channel_sort", "Firefox Channel Ascending"),
        ("-firefox_channel_sort", "Firefox Channel Descending"),
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
    paginate_by = settings.EXPERIMENTS_PAGINATE_BY

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

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            firefox_channel_sort=Experiment.firefox_channel_sort()
        )
        return qs

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
        initial["owner"] = self.request.user.id
        return initial


class ExperimentOverviewUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentOverviewForm
    next_view_name = "experiments-variants-update"
    template_name = "experiments/edit_overview.html"


class ExperimentVariantsUpdateView(ExperimentFormMixin, UpdateView):
    next_view_name = "experiments-objectives-update"
    template_name = "experiments/edit_variants.html"

    def get_form_class(self):
        if self.object.is_addon_experiment:
            return ExperimentVariantsAddonForm
        elif self.object.is_pref_experiment:
            return ExperimentVariantsPrefForm


class ExperimentObjectivesUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentObjectivesForm
    next_view_name = "experiments-risks-update"
    template_name = "experiments/edit_objectives.html"


class ExperimentRisksUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentRisksForm
    next_view_name = "experiments-detail"
    template_name = "experiments/edit_risks.html"


class ExperimentDetailView(ExperimentFormMixin, ModelFormMixin, DetailView):
    model = Experiment
    form_class = ExperimentReviewForm

    def get_template_names(self):
        return [
            "experiments/detail_{status}.html".format(
                status=self.object.status.lower()  # OSX is case insensitive
            ),
            "experiments/detail_base.html",
        ]

    def get_context_data(self, *args, **kwargs):
        if "normandy_id" in self.request.GET:
            normandy_id_form = NormandyIdForm(
                request=self.request,
                data=self.request.GET,
                instance=self.object,
            )
        else:
            normandy_id_form = NormandyIdForm(
                request=self.request, instance=self.object
            )

        return super().get_context_data(
            normandy_id_form=normandy_id_form, *args, **kwargs
        )


class ExperimentStatusUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentStatusForm
    model = Experiment

    def form_invalid(self, form):
        return redirect(
            reverse("experiments-detail", kwargs={"slug": self.object.slug})
        )


class ExperimentReviewUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentReviewForm
    model = Experiment


class ExperimentArchiveUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentArchiveForm
    model = Experiment


class ExperimentSubscribedUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentSubscribedForm
    model = Experiment


class ExperimentNormandyUpdateView(ExperimentFormMixin, UpdateView):
    form_class = NormandyIdForm
    model = Experiment

    def form_valid(self, form):
        response = super().form_valid(form)
        status_form = ExperimentStatusForm(
            request=self.request,
            data={"status": Experiment.STATUS_ACCEPTED},
            instance=self.object,
        )
        status_form.save()
        return response

    def form_invalid(self, form):
        return redirect(
            "{url}?normandy_id={value}".format(
                url=reverse(
                    "experiments-detail", kwargs={"slug": self.kwargs["slug"]}
                ),
                value=form.data["normandy_id"],
            )
        )


class ExperimentCommentCreateView(ExperimentFormMixin, CreateView):
    form_class = ExperimentCommentForm

    def form_valid(self, form):
        comment = form.save()
        return redirect(
            "{url}#{section}-comments".format(
                url=reverse(
                    "experiments-detail", kwargs={"slug": self.kwargs["slug"]}
                ),
                section=comment.section,
            )
        )

    def form_invalid(self, form):
        return redirect(
            reverse("experiments-detail", kwargs={"slug": self.kwargs["slug"]})
        )
