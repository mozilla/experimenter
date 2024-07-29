import django_filters
from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.functions import Concat

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureConfig
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
    DATES_UP = "_start_date"
    DATES_DOWN = "-_start_date"


class MultiSelectWidget(forms.SelectMultiple):
    template_name = "common/sidebar_select.html"

    def __init__(self, *args, attrs, **kwargs):
        self.icon = kwargs.pop("icon", None)
        attrs.update(
            {
                "class": "selectpicker form-control bg-body-tertiary",
                "data-live-search": "true",
            }
        )
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
        widget=MultiSelectWidget(
            icon="fa-solid fa-flask-vial",
            attrs={
                "title": "All Types",
            },
        ),
    )
    application = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Application.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-desktop",
            attrs={
                "title": "All Applications",
            },
        ),
    )
    channel = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Channel.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-road",
            attrs={
                "title": "All Channels",
            },
        ),
    )
    firefox_min_version = django_filters.MultipleChoiceFilter(
        choices=reversed(NimbusExperiment.Version.choices),
        widget=MultiSelectWidget(
            icon="fa-solid fa-code-branch",
            attrs={
                "title": "All Versions",
            },
        ),
    )
    feature_configs = django_filters.ModelMultipleChoiceFilter(
        queryset=NimbusFeatureConfig.objects.all().order_by("application", "slug"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-boxes-stacked",
            attrs={
                "title": "All Features",
            },
        ),
    )
    countries = django_filters.ModelMultipleChoiceFilter(
        queryset=Country.objects.all().order_by("code"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-globe",
            attrs={
                "title": "All Countries",
            },
        ),
    )
    languages = django_filters.ModelMultipleChoiceFilter(
        queryset=Language.objects.all().order_by("code"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-language",
            attrs={
                "title": "All Languages",
            },
        ),
    )
    locales = django_filters.ModelMultipleChoiceFilter(
        queryset=Locale.objects.all().order_by("code"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-earth-americas",
            attrs={
                "title": "All Locales",
            },
        ),
    )
    targeting_config_slug = django_filters.MultipleChoiceFilter(
        choices=sorted(TargetingConstants.TargetingConfig.choices),
        widget=MultiSelectWidget(
            icon="fa-solid fa-users-rectangle",
            attrs={
                "title": "All Audiences",
            },
        ),
    )
    projects = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all().order_by("slug"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-person-chalkboard",
            attrs={
                "title": "All Projects",
            },
        ),
    )
    qa_status = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.QAStatus.choices,
        widget=MultiSelectWidget(
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
        widget=MultiSelectWidget(
            icon="fa-solid fa-list-check",
            attrs={
                "title": "All Takeaways",
            },
        ),
    )
    owner = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.order_by("email"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-users",
            attrs={
                "title": "All Owners",
            },
        ),
    )
    subscribers = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.order_by("email"),
        widget=MultiSelectWidget(
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
