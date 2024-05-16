from collections import defaultdict

import django_filters
from django.conf import settings
from django.db import models
from django.views.generic import DetailView
from django_filters.views import FilterView

from experimenter.experiments.models import NimbusExperiment


class StatusChoices(models.TextChoices):
    DRAFT = NimbusExperiment.Status.DRAFT.value
    PREVIEW = NimbusExperiment.Status.PREVIEW.value
    LIVE = NimbusExperiment.Status.LIVE.value
    COMPLETE = NimbusExperiment.Status.COMPLETE.value
    REVIEW = "Review"
    ARCHIVED = "Archived"
    MY_EXPERIMENTS = "MyExperiments"


class NimbusExperimentFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=StatusChoices.choices, method="filter_status"
    )

    class Meta:
        model = NimbusExperiment
        fields = ["status"]

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


class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    context_object_name = "experiment"
    template_name = "changelog/overview.html"


class NimbusExperimentsListView(FilterView):
    model = NimbusExperiment
    queryset = NimbusExperiment.objects.with_owner_features()
    filterset_class = NimbusExperimentFilter
    context_object_name = "experiments"
    template_name = "nimbus_experiments/list.html"
    paginate_by = settings.EXPERIMENTS_PAGINATE_BY

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)

        query = self.request.GET.copy()
        if "status" not in query or not query["status"]:
            query["status"] = StatusChoices.LIVE.value
        kwargs["data"] = query

        return kwargs

    def get_context_data(self, **kwargs):
        queryset = self.get_queryset()
        status_counts = defaultdict(int)
        for experiment in queryset:
            if experiment.owner == self.request.user:
                status_counts[StatusChoices.MY_EXPERIMENTS.value] += 1
            if experiment.is_archived:
                status_counts[StatusChoices.ARCHIVED.value] += 1
                continue
            if (
                experiment.status == NimbusExperiment.Status.DRAFT
                and experiment.publish_status == NimbusExperiment.PublishStatus.REVIEW
            ):
                status_counts[StatusChoices.REVIEW.value] += 1
            else:
                status_counts[experiment.status] += 1

        return super().get_context_data(
            active_status=kwargs["filter"].data["status"],
            status_counts=status_counts,
            **kwargs,
        )
