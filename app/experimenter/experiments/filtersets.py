import django_filters as filters
import django_filters.widgets as widgets
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.db.models import F, IntegerField, Q
from django.db.models.expressions import Func, Value
from django.db.models.functions import Cast

from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.models import Experiment
from experimenter.projects.models import Project

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
            attrs={"class": "form-control", "placeholder": "Search Deliveries"}
        ),
    )
    type = filters.MultipleChoiceFilter(
        choices=Experiment.TYPE_CHOICES,
        conjoined=False,
        widget=forms.SelectMultiple(
            attrs={"class": "form-control", "data-none-selected-text": "All Types"}
        ),
    )
    projects = filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        null_label="No Projects",
        widget=forms.SelectMultiple(
            attrs={"class": "form-control", "data-none-selected-text": "All Projects"}
        ),
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
    owner = filters.ModelChoiceFilter(
        empty_label="All Owners",
        queryset=get_user_model().objects.all().order_by("email"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    analysis_owner = filters.ModelChoiceFilter(
        empty_label="All Data Scientists",
        queryset=get_user_model()
        .objects.all()
        .filter(
            id__in=Experiment.objects.all().values_list("analysis_owner__id", flat=True)
        )
        .order_by("email"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    archived = filters.BooleanFilter(
        label="Show archived deliveries",
        widget=forms.CheckboxInput(),
        method="archived_filter",
    )
    experiment_date_field = filters.ChoiceFilter(
        empty_label="No Date Restriction",
        choices=[
            (Experiment.EXPERIMENT_STARTS, "Delivery Starts"),
            (Experiment.EXPERIMENT_PAUSES, "Delivery Pauses"),
            (Experiment.EXPERIMENT_ENDS, "Delivery Ends"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
        method="experiment_date_field_filter",
    )
    date_range = filters.DateFromToRangeFilter(
        method="date_range_filter",
        widget=DateRangeWidget(attrs={"type": "date", "class": "form-control"}),
    )

    in_qa = filters.BooleanFilter(
        label="Show only deliveries in QA",
        widget=forms.CheckboxInput(),
        method="in_qa_filter",
    )

    surveys = filters.BooleanFilter(
        label="Show deliveries with surveys",
        widget=forms.CheckboxInput(),
        method="surveys_filter",
    )

    subscribed = filters.BooleanFilter(
        label="Show subscribed deliveries",
        widget=forms.CheckboxInput(),
        method="subscribed_filter",
    )

    longrunning = filters.BooleanFilter(
        label="Show long-running deliveries",
        widget=forms.CheckboxInput(),
        method="longrunning_filter",
    )

    is_paused = filters.BooleanFilter(
        label="Show enrollment complete deliveries",
        widget=forms.CheckboxInput(),
        method="is_paused_filter",
    )

    completed_results = filters.BooleanFilter(
        label="Show deliveries with results completed",
        widget=forms.CheckboxInput(),
        method="completed_results_filter",
    )

    class Meta:
        model = Experiment
        fields = (
            "search",
            "type",
            "projects",
            "status",
            "firefox_channel",
            "firefox_version",
            "owner",
            "analysis_owner",
            "in_qa",
            "surveys",
            "archived",
            "subscribed",
            "longrunning",
            "is_paused",
            "completed_results",
        )

    def filter_search(self, queryset, name, value):
        vector = SearchVector(
            "name",
            "short_description",
            "owner__email",
            "analysis_owner__email",
            "slug",
            "related_work",
            "addon_experiment_id",
            "pref_name",
            "public_description",
            "objectives",
            "analysis",
            "engineering_owner",
            "bugzilla_id",
            "recipe_slug",
            "data_science_issue_url",
            "feature_bugzilla_url",
        )

        query = SearchQuery(value)

        return (
            queryset.annotate(rank=SearchRank(vector, query), search=vector)
            .filter(search=value)
            .order_by("-rank")
        )

    def archived_filter(self, queryset, name, value):
        if not value:
            return queryset.exclude(archived=True)
        return queryset

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
        if date_type:
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
        return queryset

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
                            Value(ExperimentConstants.VERSION_REGEX.pattern),
                            function="substring",
                        ),
                        IntegerField(),
                    ),
                    firefox_max_int=Cast(
                        Func(
                            F("firefox_max_version"),
                            Value(ExperimentConstants.VERSION_REGEX.pattern),
                            function="substring",
                        ),
                        IntegerField(),
                    ),
                    version_count=F("firefox_max_int") - F("firefox_min_int"),
                )
                .filter(version_count__gte=3)
            )

        return queryset

    def is_paused_filter(self, queryset, name, value):
        if value:
            return queryset.filter(is_paused=True, status=Experiment.STATUS_LIVE)

        return queryset

    def completed_results_filter(self, queryset, name, value):
        if value:
            return queryset.exclude(
                Q(results_url="") | Q(results_url=None),
                Q(results_initial="") | Q(results_initial=None),
                Q(results_lessons_learned="") | Q(results_lessons_learned=None),
            )
        return queryset

    def get_type_display_value(self):
        return ", ".join(
            [
                dict(Experiment.TYPE_CHOICES)[type].replace(" Experiment", "")
                for type in self.data.getlist("type")
            ]
        )

    def get_project_display_value(self):
        project_ids = self.data.getlist("projects")

        if project_ids:
            if "null" in project_ids:
                project_ids.remove("null")
            project_name_list = Project.objects.filter(id__in=project_ids).values_list(
                "name"
            )
            if project_name_list:
                return ", ".join(project_name[0] for project_name in project_name_list)
            return "No Projects"

    def get_owner_display_value(self):
        user_id = self.data.get("owner")

        if user_id is not None:
            return str(get_user_model().objects.get(id=user_id))

    def get_display_start_date_info(self):
        experiment_date_field = self.data.get("experiment_date_field")
        date_after = self.data.get("date_range_after")
        date_before = self.data.get("date_range_before")

        if date_after and date_before:
            return f"{experiment_date_field} between {date_after} and {date_before}"
        elif date_after and date_before == "":
            return f"{experiment_date_field} after {date_after}"
        elif date_after == "" and date_before:
            return f"{experiment_date_field} before {date_before}"
        else:
            return ""
