import django_filters
from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.functions import Concat

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureConfig
from experimenter.nimbus_ui.forms import MultiSelectWidget
from experimenter.projects.models import Project
from experimenter.targeting.constants import TargetingConstants


class StatusChoices(models.TextChoices):
    DRAFT = NimbusExperiment.Status.DRAFT
    PREVIEW = NimbusExperiment.Status.PREVIEW
    LIVE = NimbusExperiment.Status.LIVE
    COMPLETE = NimbusExperiment.Status.COMPLETE
    REVIEW = "Review"
    ARCHIVED = "Archived"
    MY_EXPERIMENTS = "MyExperiments"


STATUS_FILTERS = {
    StatusChoices.DRAFT: lambda request: Q(
        is_archived=False, status=NimbusExperiment.Status.DRAFT
    ),
    StatusChoices.PREVIEW: lambda request: Q(
        is_archived=False, status=NimbusExperiment.Status.PREVIEW
    ),
    StatusChoices.LIVE: lambda request: Q(
        is_archived=False, status=NimbusExperiment.Status.LIVE
    ),
    StatusChoices.COMPLETE: lambda request: Q(
        is_archived=False, status=NimbusExperiment.Status.COMPLETE
    ),
    StatusChoices.REVIEW: lambda request: (
        Q(is_archived=False) & ~Q(publish_status=NimbusExperiment.PublishStatus.IDLE)
    ),
    StatusChoices.ARCHIVED: lambda request: Q(is_archived=True),
    StatusChoices.MY_EXPERIMENTS: lambda request: (
        Q(owner=request.user) | Q(subscribers=request.user)
    ),
}


class TypeChoices(models.TextChoices):
    ROLLOUT = "Rollout"
    EXPERIMENT = "Experiment"
    LABS = "Labs"


class SortChoices(models.TextChoices):
    NAME_UP = "name"
    NAME_DOWN = "-name"
    QA_UP = "qa_status"
    QA_DOWN = "-qa_status"
    APPLICATION_UP = "application"
    APPLICATION_DOWN = "-application"
    CHANNEL_UP = "channel"
    CHANNEL_DOWN = "-channel"
    SIZE_UP = "population_percent"
    SIZE_DOWN = "-population_percent"
    FEATURES_UP = "feature_configs__slug"
    FEATURES_DOWN = "-feature_configs__slug"
    VERSIONS_UP = "firefox_min_version"
    VERSIONS_DOWN = "-firefox_min_version"
    START_DATE_UP = "_start_date"
    START_DATE_DOWN = "-_start_date"
    END_DATE_UP = "_computed_end_date"
    END_DATE_DOWN = "-_computed_end_date"


class IconMultiSelectWidget(MultiSelectWidget):
    template_name = "common/sidebar_select.html"
    class_attrs = "selectpicker form-control bg-body-tertiary"

    def __init__(self, *args, attrs, **kwargs):
        self.icon = kwargs.pop("icon", None)
        super().__init__(*args, attrs=attrs, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["icon"] = self.icon
        return context


class NimbusExperimentFilter(django_filters.FilterSet):
    sort = django_filters.ChoiceFilter(
        method="filter_sort",
        choices=SortChoices.choices,
        widget=forms.widgets.HiddenInput,
    )
    status = django_filters.ChoiceFilter(
        method="filter_status",
        choices=StatusChoices.choices,
        widget=forms.widgets.HiddenInput,
    )
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.widgets.TextInput(
            attrs={
                "class": "form-control mb-2 bg-body-tertiary",
                "placeholder": "🔎 Search",
            }
        ),
    )
    type = django_filters.MultipleChoiceFilter(
        method="filter_type",
        choices=TypeChoices.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-flask-vial",
            attrs={
                "title": "All Types",
            },
        ),
    )
    application = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Application.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-desktop",
            attrs={
                "title": "All Applications",
            },
        ),
    )
    channel = django_filters.MultipleChoiceFilter(
        method="filter_channel",
        choices=NimbusExperiment.Channel.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-road",
            attrs={
                "title": "All Channels",
            },
        ),
    )
    firefox_min_version = django_filters.MultipleChoiceFilter(
        choices=reversed(NimbusExperiment.Version.choices),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-code-branch",
            attrs={
                "title": "All Versions",
            },
        ),
    )
    feature_configs = django_filters.ModelMultipleChoiceFilter(
        queryset=NimbusFeatureConfig.objects.all().order_by("application", "slug"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-boxes-stacked",
            attrs={
                "title": "All Features",
            },
        ),
    )
    countries = django_filters.ModelMultipleChoiceFilter(
        queryset=Country.objects.all().order_by("code"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-globe",
            attrs={
                "title": "All Countries",
            },
        ),
    )
    languages = django_filters.ModelMultipleChoiceFilter(
        queryset=Language.objects.all().order_by("code"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-language",
            attrs={
                "title": "All Languages",
            },
        ),
    )
    locales = django_filters.ModelMultipleChoiceFilter(
        queryset=Locale.objects.all().order_by("code"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-earth-americas",
            attrs={
                "title": "All Locales",
            },
        ),
    )
    targeting_config_slug = django_filters.MultipleChoiceFilter(
        choices=sorted(TargetingConstants.TargetingConfig.choices),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-users-rectangle",
            attrs={
                "title": "All Audiences",
            },
        ),
    )
    projects = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all().order_by("slug"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-person-chalkboard",
            attrs={
                "title": "All Projects",
            },
        ),
    )
    qa_status = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.QAStatus.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-user-shield",
            attrs={
                "title": "All QA Statuses",
            },
        ),
    )
    takeaways = django_filters.MultipleChoiceFilter(
        method="filter_takeaways",
        choices=[
            *NimbusExperiment.Takeaways.choices,
            *NimbusExperiment.ConclusionRecommendation.choices,
        ],
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-list-check",
            attrs={
                "title": "All Takeaways",
            },
        ),
    )
    owner = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.order_by("email"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-users",
            attrs={
                "title": "All Owners",
            },
        ),
    )
    subscribers = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.order_by("email"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-bell",
            attrs={
                "title": "All Subscribers",
            },
        ),
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "sort",
            "status",
            "search",
            "type",
            "application",
            "channel",
            "firefox_min_version",
            "feature_configs",
            "countries",
            "languages",
            "locales",
            "targeting_config_slug",
            "projects",
            "qa_status",
            "takeaways",
            "owner",
            "subscribers",
        ]

    def filter_sort(self, queryset, name, value):
        return queryset.order_by(value)

    def filter_status(self, queryset, name, value):
        return queryset.filter(STATUS_FILTERS[value](self.request))

    def filter_search(self, queryset, name, value):
        search_fields = Concat(
            "name",
            "slug",
            "public_description",
            "hypothesis",
            "takeaways_summary",
            "qa_comment",
            output_field=models.TextField(),
        )

        return queryset.annotate(search_fields=search_fields).filter(
            search_fields__icontains=value
        )

    def filter_type(self, queryset, name, value):
        query = Q()
        if TypeChoices.EXPERIMENT in value:
            query |= Q(is_rollout=False)
        if TypeChoices.ROLLOUT in value:
            query |= Q(is_rollout=True)
        if TypeChoices.LABS in value:
            query |= Q(is_firefox_labs_opt_in=True)
        return queryset.filter(query)

    def filter_takeaways(self, queryset, name, values):
        query = Q()
        for value in values:
            if value == NimbusExperiment.Takeaways.QBR_LEARNING:
                query |= Q(takeaways_qbr_learning=True)
            elif value == NimbusExperiment.Takeaways.DAU_GAIN:
                query |= Q(takeaways_metric_gain=True)
            elif value in NimbusExperiment.ConclusionRecommendation:
                query |= Q(conclusion_recommendations__contains=[value])
        return queryset.filter(query)

    def filter_channel(self, queryset, name, value):
        query = Q(channel__in=value)
        for channel in value:
            query |= Q(channels__contains=[channel])
        return queryset.filter(query)


class MyDeliveriesChoices(models.TextChoices):
    ALL = "AllDeliveries", "All My Deliveries"
    OWNED = "AllOwned", "All Owned"
    SUBSCRIBED = "AllSubscribed", "All Subscribed"


class HomeSortChoices(models.TextChoices):
    NAME_UP = "name", "Name"
    NAME_DOWN = "-name", "Name"
    STATUS_UP = "status", "Status"
    STATUS_DOWN = "-status", "Status"
    QA_UP = "qa_status", "QA"
    QA_DOWN = "-qa_status", "QA"
    APPLICATION_UP = "application", "Application"
    APPLICATION_DOWN = "-application", "Application"
    TYPE_UP = "is_rollout", "Type"
    TYPE_DOWN = "-is_rollout", "Type"
    CHANNEL_UP = "channel", "Channel"
    CHANNEL_DOWN = "-channel", "Channel"
    SIZE_UP = "population_percent", "Size"
    SIZE_DOWN = "-population_percent", "Size"
    DATES_UP = "_start_date", "Dates"
    DATES_DOWN = "-_start_date", "Dates"
    VERSIONS_UP = "firefox_min_version", "Versions"
    VERSIONS_DOWN = "-firefox_min_version", "Versions"
    FEATURES_UP = "feature_configs__slug", "Features"
    FEATURES_DOWN = "-feature_configs__slug", "Features"
    RESULTS_UP = "results_data", "Results"
    RESULTS_DOWN = "-results_data", "Results"


HOME_SORTABLE_HEADERS = []
seen = set()

for choice in HomeSortChoices:
    field = choice.value.lstrip("-")
    if field not in seen:
        HOME_SORTABLE_HEADERS.append((field, choice.label))
        seen.add(field)


class NimbusExperimentsHomeFilter(django_filters.FilterSet):
    my_deliveries_status = django_filters.ChoiceFilter(
        label="",
        method="filter_my_deliveries",
        choices=MyDeliveriesChoices.choices,
        empty_label=None,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    sort = django_filters.ChoiceFilter(
        method="filter_sort",
        choices=HomeSortChoices.choices,
        widget=forms.HiddenInput,
    )

    class Meta:
        model = NimbusExperiment
        fields = ["my_deliveries_status", "sort"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get("my_deliveries_status"):
            self.filters["my_deliveries_status"].field.initial = MyDeliveriesChoices.ALL

    def filter_my_deliveries(self, queryset, name, value):
        user = self.request.user

        match value:
            case MyDeliveriesChoices.OWNED:
                return queryset.filter(owner=user)
            case MyDeliveriesChoices.SUBSCRIBED:
                return queryset.filter(subscribers=user)
            case _:
                return queryset  # Default = All Deliveries

    def filter_sort(self, queryset, name, value):
        return queryset.order_by(value)
