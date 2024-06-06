from django.conf import settings
from django.views.generic import DetailView
from django_filters.views import FilterView

from experimenter.experiments.models import NimbusExperiment
from experimenter.nimbus_ui_new.filtersets import (
    NimbusExperimentFilter,
    SortChoices,
    StatusChoices,
)


class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    context_object_name = "experiment"
    template_name = "changelog/overview.html"


class NimbusExperimentsListView(FilterView):
    model = NimbusExperiment
    queryset = (
        NimbusExperiment.objects.all()
        .order_by("-_updated_date_time")
        .prefetch_related("feature_configs")
    )
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
        archived = queryset.filter(is_archived=True)
        unarchived = queryset.filter(is_archived=False)
        status_counts = {
            StatusChoices.DRAFT: unarchived.filter(
                status=NimbusExperiment.Status.DRAFT,
                publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).count(),
            StatusChoices.PREVIEW: unarchived.filter(
                status=NimbusExperiment.Status.PREVIEW
            ).count(),
            StatusChoices.LIVE: unarchived.filter(
                status=NimbusExperiment.Status.LIVE
            ).count(),
            StatusChoices.COMPLETE: unarchived.filter(
                status=NimbusExperiment.Status.COMPLETE
            ).count(),
            StatusChoices.REVIEW: unarchived.filter(
                publish_status=NimbusExperiment.PublishStatus.REVIEW
            ).count(),
            StatusChoices.ARCHIVED: archived.count(),
            StatusChoices.MY_EXPERIMENTS: queryset.filter(
                owner=self.request.user
            ).count(),
        }

        return super().get_context_data(
            active_status=kwargs["filter"].data["status"],
            status_counts=status_counts,
            sort_choices=SortChoices,
            **kwargs,
        )


class NimbusExperimentsListTableView(NimbusExperimentsListView):
    template_name = "nimbus_experiments/table.html"

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        response.headers["HX-Push"] = f"?{self.request.GET.urlencode()}"
        return response
