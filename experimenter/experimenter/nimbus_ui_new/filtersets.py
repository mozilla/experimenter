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

    def __init__(self, *args, **kwargs):
        self.icon = kwargs.pop("icon", None)
        super().__init__(*args, **kwargs)

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
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    application = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Application.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-desktop",
            attrs={
                "title": "All Applications",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    channel = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Channel.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-road",
            attrs={
                "title": "All Channels",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    firefox_min_version = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Version.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-code-branch",
            attrs={
                "title": "All Versions",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    feature_configs = django_filters.ModelMultipleChoiceFilter(
        queryset=NimbusFeatureConfig.objects.all(),
        widget=MultiSelectWidget(
            icon="fa-solid fa-boxes-stacked",
            attrs={
                "title": "All Features",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    countries = django_filters.ModelMultipleChoiceFilter(
        queryset=Country.objects.all(),
        widget=MultiSelectWidget(
            icon="fa-solid fa-globe",
            attrs={
                "title": "All Countries",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    languages = django_filters.ModelMultipleChoiceFilter(
        queryset=Language.objects.all(),
        widget=MultiSelectWidget(
            icon="fa-solid fa-language",
            attrs={
                "title": "All Languages",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    locales = django_filters.ModelMultipleChoiceFilter(
        queryset=Locale.objects.all(),
        widget=MultiSelectWidget(
            icon="fa-solid fa-earth-americas",
            attrs={
                "title": "All Locales",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    targeting_config_slug = django_filters.MultipleChoiceFilter(
        choices=TargetingConstants.TargetingConfig.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-users-rectangle",
            attrs={
                "title": "All Audiences",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    projects = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        widget=MultiSelectWidget(
            icon="fa-solid fa-person-chalkboard",
            attrs={
                "title": "All Projects",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    qa_status = django_filters.MultipleChoiceFilter(
        choices=NimbusExperiment.QAStatus.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-user-shield",
            attrs={
                "title": "All QA Statuses",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    takeaways = django_filters.MultipleChoiceFilter(
        method="filter_takeaways",
        choices=NimbusExperiment.Takeaways.choices
        + NimbusExperiment.ConclusionRecommendation.choices,
        widget=MultiSelectWidget(
            icon="fa-solid fa-list-check",
            attrs={
                "title": "All Takeaways",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    owner = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.order_by("email"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-users",
            attrs={
                "title": "All Owners",
                "class": "selectpicker",
                "data-live-search": "true",
            },
        ),
    )
    subscribers = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.order_by("email"),
        widget=MultiSelectWidget(
            icon="fa-solid fa-bell",
            attrs={
                "title": "All Subscribers",
                "class": "selectpicker",
                "data-live-search": "true",
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
        match value:
            case StatusChoices.REVIEW:
                return queryset.filter(
                    status=NimbusExperiment.Status.DRAFT,
                    publish_status=NimbusExperiment.PublishStatus.REVIEW,
                )
            case StatusChoices.ARCHIVED:
                return queryset.filter(is_archived=True)
            case StatusChoices.MY_EXPERIMENTS:
                return queryset.filter(owner=self.request.user)
            case _:
                return queryset.filter(
                    status=value,
                    is_archived=False,
                ).exclude(publish_status=NimbusExperiment.PublishStatus.REVIEW)

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

    def filter_takeaways(self, queryset, name, value):
        query = Q()
        for val in value:
            if val in dict(NimbusExperiment.Takeaways.choices):
                if val == NimbusExperiment.Takeaways.QBR_LEARNING:
                    query |= Q(takeaways_qbr_learning=True)
                elif val == NimbusExperiment.Takeaways.DAU_GAIN:
                    query |= Q(takeaways_metric_gain=True)
            elif val in dict(NimbusExperiment.ConclusionRecommendation.choices):
                query |= Q(conclusion_recommendations__contains=[val])
        return queryset.filter(query)
