from django.conf import settings
from django.shortcuts import render
from django.views.generic import DetailView
from django_filters.views import FilterView

from experimenter.experiments.constants import RISK_QUESTIONS
from experimenter.experiments.forms import QAStatusForm
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

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)

        # Create a second filterset with the status removed from data
        # to count experiments with all other filters applied except status
        kwargs_no_status = kwargs.copy()
        kwargs_no_status["data"] = kwargs_no_status["data"].copy()
        kwargs_no_status["data"].pop("status")
        self.filterset_no_status = filterset_class(**kwargs_no_status)

        return filterset_class(**kwargs)

    def get_context_data(self, **kwargs):
        all_statuses = self.filterset_no_status.qs
        archived = all_statuses.filter(is_archived=True)
        unarchived = all_statuses.filter(is_archived=False)
        status_counts = {
            StatusChoices.DRAFT: unarchived.filter(
                status=NimbusExperiment.Status.DRAFT,
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
            StatusChoices.MY_EXPERIMENTS: all_statuses.filter(
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


class NimbusExperimentDetailView(DetailView):
    model = NimbusExperiment
    template_name = "nimbus_experiments/detail.html"
    context_object_name = "experiment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["RISK_QUESTIONS"] = RISK_QUESTIONS

        primary_outcomes = self.object.primary_outcomes
        secondary_outcomes = self.object.secondary_outcomes
        doc_base_url = "https://mozilla.github.io/metric-hub/outcomes/"
        context["primary_outcome_links"] = [
            (outcome, f"{doc_base_url}{self.object.application}/{outcome}")
            for outcome in primary_outcomes
        ]
        context["secondary_outcome_links"] = [
            (outcome, f"{doc_base_url}{self.object.application}/{outcome}")
            for outcome in secondary_outcomes
        ]
        context["qa_edit_mode"] = self.request.GET.get("edit_qa_status") == "true"
        if context["qa_edit_mode"]:
            context["form"] = QAStatusForm(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = QAStatusForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            context = self.get_context_data(object=self.object)
            return render(request, self.template_name, context)
        else:
            # if form is not valid, still prepare context data
            context = self.get_context_data(object=self.object)
            context["form"] = form
            context["qa_edit_mode"] = True
            return render(request, self.template_name, context)
