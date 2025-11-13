from datetime import date, datetime, timedelta

import django_filters
from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.functions import Concat

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureConfig, Tag
from experimenter.nimbus_ui.forms import MultiSelectWidget
from experimenter.targeting.constants import TargetingConstants


class VersionSortMixin:
    def _get_version_sort_key(self, experiment):
        if experiment.firefox_min_version:
            return NimbusConstants.Version.parse(experiment.firefox_min_version)
        return NimbusConstants.Version.parse(NimbusConstants.Version.NO_VERSION)

    def sort_by_version(self, queryset, reverse=False):
        experiments = list(queryset)
        experiments.sort(key=self._get_version_sort_key, reverse=reverse)
        sorted_ids = [e.id for e in experiments]
        preserved_order = models.Case(
            *[models.When(pk=pk, then=pos) for pos, pk in enumerate(sorted_ids)]
        )
        return queryset.filter(id__in=sorted_ids).order_by(preserved_order)


class StatusChoices(models.TextChoices):
    DRAFT = NimbusExperiment.Status.DRAFT
    PREVIEW = NimbusExperiment.Status.PREVIEW
    LIVE = NimbusExperiment.Status.LIVE
    COMPLETE = NimbusExperiment.Status.COMPLETE
    REVIEW = "Review"
    ARCHIVED = "Archived"
    MY_EXPERIMENTS = "MyExperiments"


class HomeStatusChoices(models.TextChoices):
    DRAFT = NimbusExperiment.Status.DRAFT
    PREVIEW = NimbusExperiment.Status.PREVIEW
    LIVE = NimbusExperiment.Status.LIVE
    COMPLETE = NimbusExperiment.Status.COMPLETE
    REVIEW = NimbusExperiment.PublishStatus.REVIEW


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
    CHANNEL_UP = "merged_channel"
    CHANNEL_DOWN = "-merged_channel"
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


class DateRangeChoices(models.TextChoices):
    LAST_7_DAYS = "last_7_days", "Last 7 Days"
    LAST_30_DAYS = "last_30_days", "Last 30 Days"
    LAST_3_MONTHS = "last_3_months", "Last 3 Months"
    LAST_6_MONTHS = "last_6_months", "Last 6 Months"
    THIS_YEAR = "this_year", "This Year"
    CUSTOM = "custom", "Custom Date Range"


class NimbusExperimentFilter(VersionSortMixin, django_filters.FilterSet):
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
        choices=list(reversed(NimbusExperiment.Version.choices)),
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
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.order_by("name"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-tags",
            attrs={
                "title": "All Tags",
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
            "qa_status",
            "takeaways",
            "owner",
            "subscribers",
            "tags",
        ]

    def filter_sort(self, queryset, name, value):
        if value in (SortChoices.VERSIONS_UP, SortChoices.VERSIONS_DOWN):
            return self.sort_by_version(
                queryset, reverse=(value == SortChoices.VERSIONS_DOWN)
            )

        return queryset.order_by(value, "slug")

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
            query |= Q(is_rollout=False, is_firefox_labs_opt_in=False)
        if TypeChoices.ROLLOUT in value:
            query |= Q(is_rollout=True, is_firefox_labs_opt_in=False)
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
    SUBSCRIBED = "AllSubscribed", "All Subscribed Deliveries"
    FEATURE_SUBSCRIBED = "FeatureSubscribed", "All Subscribed Features"


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
    CHANNEL_UP = "merged_channel", "Channel"
    CHANNEL_DOWN = "-merged_channel", "Channel"
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

    @staticmethod
    def sortable_headers():
        seen = set()
        headers = []
        for choice in HomeSortChoices:
            field = choice.value.lstrip("-")
            if field not in seen:
                headers.append((field, choice.label))
                seen.add(field)
        return headers


class NimbusExperimentsHomeFilter(VersionSortMixin, django_filters.FilterSet):
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
    status = django_filters.MultipleChoiceFilter(
        method="filter_status",
        choices=HomeStatusChoices.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-circle-dot",
            attrs={"title": "All Statuses"},
        ),
    )
    type = django_filters.MultipleChoiceFilter(
        method="filter_type",
        choices=NimbusConstants.HomeTypeChoices.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-flask-vial",
            attrs={
                "title": "All Types",
            },
        ),
    )
    qa_status = django_filters.MultipleChoiceFilter(
        method="filter_qa_status",
        choices=NimbusExperiment.QAStatus.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-user-shield",
            attrs={"title": "All QA Statuses"},
        ),
    )
    channel = django_filters.MultipleChoiceFilter(
        method="filter_channel",
        choices=NimbusExperiment.Channel.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-tv",
            attrs={"title": "All Channels"},
        ),
    )
    application = django_filters.MultipleChoiceFilter(
        method="filter_application",
        choices=NimbusConstants.Application.choices,
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-mobile-alt",
            attrs={"title": "All Applications"},
        ),
    )
    feature_configs = django_filters.ModelMultipleChoiceFilter(
        method="filter_feature_configs",
        queryset=NimbusFeatureConfig.objects.all().order_by("application", "slug"),
        widget=IconMultiSelectWidget(
            icon="fa-solid fa-boxes-stacked",
            attrs={"title": "All Features"},
        ),
    )
    date_range = django_filters.ChoiceFilter(
        choices=DateRangeChoices.choices,
        method="filter_by_date_range",
        required=False,
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "my_deliveries_status",
            "sort",
            "status",
            "type",
            "qa_status",
            "channel",
            "application",
            "feature_configs",
            "date_range",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get("my_deliveries_status"):
            self.filters["my_deliveries_status"].field.initial = MyDeliveriesChoices.ALL

        # Limit feature_configs to only features used in user's deliveries
        # or features the user is directly subscribed to
        if hasattr(self, "request") and self.request.user.is_authenticated:
            user_feature_ids = (
                NimbusExperiment.objects.filter(
                    Q(owner=self.request.user)
                    | Q(subscribers=self.request.user)
                    | Q(feature_configs__subscribers=self.request.user)
                )
                .values_list("feature_configs", flat=True)
                .distinct()
            )

            user_features = NimbusFeatureConfig.objects.filter(
                id__in=user_feature_ids
            ).order_by("application", "slug")

            if user_features.exists():
                self.filters["feature_configs"].queryset = user_features

    def filter_my_deliveries(self, queryset, name, value):
        user = self.request.user

        match value:
            case MyDeliveriesChoices.OWNED:
                return queryset.filter(owner=user)
            case MyDeliveriesChoices.SUBSCRIBED:
                return queryset.filter(subscribers=user)
            case MyDeliveriesChoices.FEATURE_SUBSCRIBED:
                return queryset.filter(feature_configs__subscribers=user)
            case _:
                return queryset  # Default = All Deliveries

    def filter_sort(self, queryset, name, value):
        if value in (HomeSortChoices.VERSIONS_UP, HomeSortChoices.VERSIONS_DOWN):
            return self.sort_by_version(
                queryset, reverse=(value == HomeSortChoices.VERSIONS_DOWN)
            )

        return queryset.order_by(value, "slug")

    def filter_status(self, queryset, name, values):
        query = Q()
        for value in values:
            if value == HomeStatusChoices.REVIEW:
                # Review: DRAFT or PREVIEW with non-IDLE publish_status
                query |= Q(
                    is_archived=False,
                    status__in=[
                        NimbusExperiment.Status.DRAFT,
                        NimbusExperiment.Status.PREVIEW,
                    ],
                    publish_status__in=[
                        NimbusExperiment.PublishStatus.REVIEW,
                        NimbusExperiment.PublishStatus.APPROVED,
                        NimbusExperiment.PublishStatus.WAITING,
                    ],
                )
            else:
                # Other statuses: status match with IDLE publish_status
                query |= Q(
                    is_archived=False,
                    status=value,
                    publish_status=NimbusExperiment.PublishStatus.IDLE,
                )
        return queryset.filter(query)

    def filter_type(self, queryset, name, values):
        query = Q()
        for v in values:
            delivery_type = NimbusConstants.HomeTypeChoices(v)

            match delivery_type:
                case NimbusConstants.HomeTypeChoices.LABS:
                    query |= Q(is_firefox_labs_opt_in=True)
                case NimbusConstants.HomeTypeChoices.ROLLOUT:
                    query |= Q(is_firefox_labs_opt_in=False, is_rollout=True)
                case NimbusConstants.HomeTypeChoices.EXPERIMENT:
                    query |= Q(is_firefox_labs_opt_in=False, is_rollout=False)

        return queryset.filter(query)

    def filter_qa_status(self, queryset, name, values):
        return queryset.filter(qa_status__in=values)

    def filter_channel(self, queryset, name, values):
        query = Q(channel__in=values)
        for value in values:
            query |= Q(channels__contains=[value])
        return queryset.filter(query)

    def filter_application(self, queryset, name, values):
        return queryset.filter(application__in=values)

    def filter_feature_configs(self, queryset, name, values):
        if not values:
            return queryset
        return queryset.filter(feature_configs__in=values).distinct()

    def filter_by_date_range(self, queryset, name, value):
        today = date.today()

        match value:
            case DateRangeChoices.LAST_7_DAYS:
                start_date = today - timedelta(days=7)
                return queryset.filter(_start_date__gte=start_date)
            case DateRangeChoices.LAST_30_DAYS:
                start_date = today - timedelta(days=30)
                return queryset.filter(_start_date__gte=start_date)
            case DateRangeChoices.LAST_3_MONTHS:
                start_date = today - timedelta(days=90)
                return queryset.filter(_start_date__gte=start_date)
            case DateRangeChoices.LAST_6_MONTHS:
                start_date = today - timedelta(days=180)
                return queryset.filter(_start_date__gte=start_date)
            case DateRangeChoices.THIS_YEAR:
                start_date = date(today.year, 1, 1)
                return queryset.filter(_start_date__gte=start_date)
            case DateRangeChoices.CUSTOM:
                # Handle custom date range - can be start only, end only, or both
                query = Q()
                start_date_value = self.data.get("start_date")
                end_date_value = self.data.get("end_date")

                # Apply start date filter if provided
                if start_date_value:
                    try:
                        parsed_start_date = datetime.strptime(
                            start_date_value, "%Y-%m-%d"
                        ).date()
                        query &= Q(_start_date__gte=parsed_start_date)
                    except (ValueError, TypeError, AttributeError):
                        pass

                # Apply end date filter if provided
                if end_date_value:
                    try:
                        parsed_end_date = datetime.strptime(
                            end_date_value, "%Y-%m-%d"
                        ).date()
                        query &= Q(_computed_end_date__lte=parsed_end_date)
                    except (ValueError, TypeError, AttributeError):
                        pass

                # Only apply filter if we have at least one valid date
                if start_date_value or end_date_value:
                    return queryset.filter(query)

        return queryset


class FeaturesPageSortChoices(models.TextChoices):
    class Deliveries(models.TextChoices):
        NAME_UP = "slug", "Recipe Name"
        NAME_DOWN = "-slug", "Recipe Name"
        DATE_UP = "_start_date", "Launch Date"
        DATE_DOWN = "-_start_date", "Launch Date"
        TYPE_UP = "is_rollout", "Delivery Type"
        TYPE_DOWN = "-is_rollout", "Delivery Type"
        CHANNEL_UP = "merged_channel", "Channel(s)"
        CHANNEL_DOWN = "-merged_channel", "Channel(s)"
        VERSIONS_UP = "firefox_min_version", "Min Version"
        VERSIONS_DOWN = "-firefox_min_version", "Min Version"
        SIZE_UP = "total_enrolled_clients", "Pop. Size"
        SIZE_DOWN = "-total_enrolled_clients", "Pop. Size"

    class QARuns(models.TextChoices):
        DATE_UP = "qa_run_date", "Date"
        DATE_DOWN = "-qa_run_date", "Date"
        TYPE_UP = "qa_run_type", "Testing Type"
        TYPE_DOWN = "-qa_run_type", "Testing Type"

    class FeatureChanges(models.TextChoices):
        VERSION_UP = "change_version", "Version"
        VERSION_DOWN = "-change_version", "Version"
        CHANGES_UP = "change_size", "Size of Changes"
        CHANGES_DOWN = "-change_size", "Size of Changes"

    @staticmethod
    def sortable_headers(table_name):
        seen = set()
        headers = []
        for choice in table_name:
            field = choice.value.lstrip("-")
            if field not in seen:
                headers.append((field, choice.label))
                seen.add(field)
        return headers
