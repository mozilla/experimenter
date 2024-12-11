from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView, DetailView
from django.views.generic.edit import UpdateView
from django_filters.views import FilterView

from experimenter.experiments.constants import EXTERNAL_URLS, RISK_QUESTIONS
from experimenter.experiments.models import (
    NimbusExperiment,
)
from experimenter.nimbus_ui_new.constants import NimbusUIConstants
from experimenter.nimbus_ui_new.filtersets import (
    STATUS_FILTERS,
    NimbusExperimentFilter,
    SortChoices,
    StatusChoices,
)
from experimenter.nimbus_ui_new.forms import (
    CancelReviewForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    LaunchPreviewToDraftForm,
    LaunchPreviewToReviewForm,
    LaunchToPreviewForm,
    LaunchWithoutPreviewForm,
    MetricsForm,
    NimbusExperimentCreateForm,
    OverviewForm,
    QAStatusForm,
    SignoffForm,
    SubscribeForm,
    TakeawaysForm,
    UnsubscribeForm,
)


class RequestFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class RenderResponseMixin:
    def form_valid(self, form):
        super().form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))


class RenderParentResponseMixin:
    def form_valid(self, form):
        super().form_valid(form)
        form = super().form_class(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form))


class NimbusExperimentViewMixin:
    model = NimbusExperiment
    context_object_name = "experiment"


class NimbusChangeLogsView(NimbusExperimentViewMixin, DetailView):
    template_name = "changelog/overview.html"


class NimbusExperimentsListView(NimbusExperimentViewMixin, FilterView):
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
        queryset = self.filterset_no_status.qs

        status_counts = {
            s: queryset.filter(STATUS_FILTERS[s](self.request)).count()
            for s in StatusChoices
        }

        return super().get_context_data(
            active_status=kwargs["filter"].data["status"],
            status_counts=status_counts,
            sort_choices=SortChoices,
            create_form=NimbusExperimentCreateForm(),
            **kwargs,
        )


class NimbusExperimentsListTableView(NimbusExperimentsListView):
    template_name = "nimbus_experiments/table.html"

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        response.headers["HX-Push"] = f"?{self.request.GET.urlencode()}"
        return response


def build_experiment_context(experiment):
    outcome_doc_base_url = "https://mozilla.github.io/metric-hub/outcomes/"
    primary_outcome_links = [
        (outcome, f"{outcome_doc_base_url}{experiment.application}/{outcome}")
        for outcome in experiment.primary_outcomes
    ]
    secondary_outcome_links = [
        (outcome, f"{outcome_doc_base_url}{experiment.application}/{outcome}")
        for outcome in experiment.secondary_outcomes
    ]

    segment_doc_base_url = "https://mozilla.github.io/metric-hub/segments/"
    segment_links = [
        (
            segment,
            # ruff prefers this implicit syntax for concatenating strings
            f"{segment_doc_base_url}"
            f"{experiment.application.replace('-', '_')}/"
            f"#{segment}",
        )
        for segment in experiment.segments
    ]
    context = {
        "RISK_QUESTIONS": RISK_QUESTIONS,
        "EXTERNAL_URLS": EXTERNAL_URLS,
        "primary_outcome_links": primary_outcome_links,
        "secondary_outcome_links": secondary_outcome_links,
        "segment_links": segment_links,
        "risk_message_url": NimbusUIConstants.RISK_MESSAGE_URL,
    }
    return context


class NimbusExperimentDetailView(NimbusExperimentViewMixin, DetailView):
    template_name = "nimbus_experiments/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment_context = build_experiment_context(self.object)
        context.update(experiment_context)
        context["qa_edit_mode"] = self.request.GET.get("edit_qa_status") == "true"
        context["takeaways_edit_mode"] = self.request.GET.get("edit_takeaways") == "true"
        if context["qa_edit_mode"]:
            context["form"] = QAStatusForm(instance=self.object)
        if context["takeaways_edit_mode"]:
            context["takeaways_form"] = TakeawaysForm(instance=self.object)
        return context


class QAStatusUpdateView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    form_class = QAStatusForm
    template_name = "nimbus_experiments/detail.html"

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        experiment_context = build_experiment_context(self.object)
        context.update(experiment_context)
        context["qa_edit_mode"] = True
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("nimbus-new-detail", kwargs={"slug": self.object.slug})


class TakeawaysUpdateView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    form_class = TakeawaysForm
    template_name = "nimbus_experiments/detail.html"

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        experiment_context = build_experiment_context(self.object)
        context.update(experiment_context)
        context["takeaways_edit_mode"] = True
        context["takeaways_form"] = form
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("nimbus-new-detail", kwargs={"slug": self.object.slug})


class SignoffUpdateView(RequestFormMixin, UpdateView):
    model = NimbusExperiment
    form_class = SignoffForm
    template_name = "nimbus_experiments/update_signoff.html"
    context_object_name = "experiment"

    def get_success_url(self):
        return reverse("nimbus-new-detail", kwargs={"slug": self.object.slug})


class NimbusExperimentsCreateView(
    NimbusExperimentViewMixin, RequestFormMixin, CreateView
):
    form_class = NimbusExperimentCreateForm
    template_name = "nimbus_experiments/create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["data"] = kwargs["data"].copy()
        kwargs["data"]["owner"] = self.request.user
        return kwargs

    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)

        if response.status_code == 302:
            response = HttpResponse()
            response.headers["HX-Redirect"] = reverse(
                "nimbus-detail", kwargs={"slug": self.object.slug}
            )
        return response


class OverviewUpdateView(
    NimbusExperimentViewMixin, RequestFormMixin, RenderResponseMixin, UpdateView
):
    form_class = OverviewForm
    template_name = "nimbus_experiments/edit_overview.html"


class DocumentationLinkCreateView(RenderParentResponseMixin, OverviewUpdateView):
    form_class = DocumentationLinkCreateForm


class DocumentationLinkDeleteView(RenderParentResponseMixin, OverviewUpdateView):
    form_class = DocumentationLinkDeleteForm


class MetricsUpdateView(
    NimbusExperimentViewMixin, RequestFormMixin, RenderResponseMixin, UpdateView
):
    form_class = MetricsForm
    template_name = "nimbus_experiments/edit_metrics.html"


class SubscribeView(
    NimbusExperimentViewMixin, RequestFormMixin, RenderResponseMixin, UpdateView
):
    form_class = SubscribeForm
    template_name = "nimbus_experiments/subscribers_list.html"


class UnsubscribeView(
    NimbusExperimentViewMixin, RequestFormMixin, RenderResponseMixin, UpdateView
):
    form_class = UnsubscribeForm
    template_name = "nimbus_experiments/subscribers_list.html"

    def form_valid(self, form):
        super().form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))


class TimelineAndControlsMixin:
    """
    Mixin to handle rendering of timeline and controls for a given experiment.
    """

    def render_response_with_timeline_and_controls(self, experiment, controls_template):
        """
        Renders both the timeline and controls together as a response.
        """
        timeline_html = render_to_string(
            "nimbus_experiments/timeline.html",
            {"experiment": experiment},
            request=self.request,
        )

        controls_html = render_to_string(
            controls_template,
            {"experiment": experiment},
            request=self.request,
        )

        return HttpResponse(
            f"""
            <div id="experiment-container">
                <div id="experiment-timeline">{timeline_html}</div>
                <div id="launch-controls">{controls_html}</div>
            </div>
            """
        )

    def form_valid(self, form):
        """
        Override form_valid to include timeline and controls in the response.
        """
        super().form_valid(form)
        experiment = self.object
        controls_template = self.get_controls_template(experiment)
        return self.render_response_with_timeline_and_controls(
            experiment, controls_template
        )


class LaunchToPreviewView(
    NimbusExperimentViewMixin, RequestFormMixin, TimelineAndControlsMixin, UpdateView
):
    form_class = LaunchToPreviewForm

    def get_controls_template(self, experiment):
        return (
            "nimbus_experiments/launch_with_preview_controls.html"
            if experiment.is_preview
            else "nimbus_experiments/launch_controls.html"
        )


class LaunchWithoutPreviewView(
    NimbusExperimentViewMixin, RequestFormMixin, TimelineAndControlsMixin, UpdateView
):
    form_class = LaunchWithoutPreviewForm

    def get_controls_template(self, experiment):
        return "nimbus_experiments/launch_without_preview_controls.html"


class LaunchPreviewToReviewView(
    NimbusExperimentViewMixin, RequestFormMixin, TimelineAndControlsMixin, UpdateView
):
    form_class = LaunchPreviewToReviewForm

    def get_controls_template(self, experiment):
        return "nimbus_experiments/review_controls.html"


class LaunchPreviewToDraftView(
    NimbusExperimentViewMixin, RequestFormMixin, TimelineAndControlsMixin, UpdateView
):
    form_class = LaunchPreviewToDraftForm

    def get_controls_template(self, experiment):
        return "nimbus_experiments/launch_controls.html"


class CancelReviewView(
    NimbusExperimentViewMixin, RequestFormMixin, TimelineAndControlsMixin, UpdateView
):
    form_class = CancelReviewForm

    def get_controls_template(self, experiment):
        return "nimbus_experiments/launch_controls.html"
