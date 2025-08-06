from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView
from django.views.generic.edit import UpdateView
from django_filters.views import FilterView

from experimenter.experiments.constants import EXTERNAL_URLS, RISK_QUESTIONS
from experimenter.experiments.models import (
    NimbusExperiment,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.nimbus_ui.filtersets import (
    STATUS_FILTERS,
    NimbusExperimentFilter,
    SortChoices,
    StatusChoices,
)
from experimenter.nimbus_ui.forms import (
    ApproveEndEnrollmentForm,
    ApproveEndExperimentForm,
    ApproveUpdateRolloutForm,
    AudienceForm,
    BranchScreenshotCreateForm,
    BranchScreenshotDeleteForm,
    CancelEndEnrollmentForm,
    CancelEndExperimentForm,
    CancelUpdateRolloutForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    DraftToPreviewForm,
    DraftToReviewForm,
    LiveToCompleteForm,
    LiveToEndEnrollmentForm,
    LiveToUpdateRolloutForm,
    MetricsForm,
    NimbusBranchCreateForm,
    NimbusBranchDeleteForm,
    NimbusBranchesForm,
    NimbusExperimentCreateForm,
    NimbusExperimentPromoteToRolloutForm,
    NimbusExperimentSidebarCloneForm,
    OverviewForm,
    PreviewToDraftForm,
    PreviewToReviewForm,
    QAStatusForm,
    ReviewToApproveForm,
    ReviewToDraftForm,
    SignoffForm,
    SubscribeForm,
    TakeawaysForm,
    ToggleArchiveForm,
    UnsubscribeForm,
)


class RequestFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class ValidationErrorsMixin:
    def get_context_data(self, **kwargs):
        experiment = self.get_object()
        field_errors = experiment.get_invalid_fields_errors()

        fields_by_page = {
            "overview": {*OverviewForm.Meta.fields},
            "branches": {
                *NimbusBranchesForm.Meta.fields,
                "treatment_branches",
                "reference_branch",
            },
            "metrics": {*MetricsForm.Meta.fields},
            "audience": {*AudienceForm.Meta.fields},
        }

        field_errors = self.get_object().get_invalid_fields_errors()
        field_error_keys = set(field_errors.keys())

        invalid_pages = []
        for page, fields in fields_by_page.items():
            if field_error_keys.intersection(fields):
                invalid_pages.append(page)

        show_errors = self.request.GET.get("show_errors") == "true"
        is_summary_view = self.request.resolver_match.view_name == "nimbus-ui-detail"

        validation_errors = {}
        if show_errors or is_summary_view:
            validation_errors = field_errors

        return super().get_context_data(
            validation_errors=validation_errors,
            is_ready_to_launch=not field_errors,
            invalid_pages=invalid_pages,
            non_page_errors=field_errors and not invalid_pages,
            **kwargs,
        )


class RenderResponseMixin:
    def form_valid(self, form):
        super().form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))


class RenderDBResponseMixin:
    def form_valid(self, form):
        super().form_valid(form)
        form = self.form_class(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form))


class RenderParentDBResponseMixin:
    def form_valid(self, form):
        super().form_valid(form)
        form = super().form_class(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form))


class NimbusExperimentViewMixin:
    model = NimbusExperiment
    context_object_name = "experiment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment = getattr(self, "object", None)

        context["sidebar_links"] = (
            experiment.sidebar_links(self.request.path)
            if experiment and experiment.slug
            else []
        )
        return context


class UpdateRedirectViewMixin:
    def can_edit(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_edit():
            return HttpResponseRedirect(
                reverse("nimbus-ui-detail", kwargs={"slug": self.object.slug})
            )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_edit():
            response = HttpResponse()
            base_url = reverse("nimbus-ui-detail", kwargs={"slug": self.object.slug})
            response.headers["HX-Redirect"] = f"{base_url}?save_failed=true"
            return response
        return super().post(request, *args, **kwargs)


class CloneExperimentFormMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clone_form"] = NimbusExperimentSidebarCloneForm(instance=self.object)
        return context


class NimbusChangeLogsView(
    NimbusExperimentViewMixin, CloneExperimentFormMixin, DetailView
):
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
        "review_url": NimbusUIConstants.REVIEW_URL,
    }
    return context


class NimbusExperimentDetailView(
    ValidationErrorsMixin,
    NimbusExperimentViewMixin,
    CloneExperimentFormMixin,
    UpdateView,
):
    template_name = "nimbus_experiments/detail.html"
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment_context = build_experiment_context(self.object)
        context.update(experiment_context)

        context["promote_to_rollout_forms"] = NimbusExperimentPromoteToRolloutForm(
            instance=self.object
        )
        context["qa_edit_mode"] = self.request.GET.get("edit_qa_status") == "true"
        context["takeaways_edit_mode"] = self.request.GET.get("edit_takeaways") == "true"
        if context["qa_edit_mode"]:
            context["form"] = QAStatusForm(instance=self.object)
        if context["takeaways_edit_mode"]:
            context["takeaways_form"] = TakeawaysForm(instance=self.object)

        if "save_failed" in self.request.GET:
            context["save_failed"] = True

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
        return reverse("nimbus-ui-detail", kwargs={"slug": self.object.slug})


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
        return reverse("nimbus-ui-detail", kwargs={"slug": self.object.slug})


class SignoffUpdateView(RequestFormMixin, UpdateView):
    model = NimbusExperiment
    form_class = SignoffForm
    template_name = "nimbus_experiments/update_signoff.html"
    context_object_name = "experiment"

    def get_success_url(self):
        return reverse("nimbus-ui-detail", kwargs={"slug": self.object.slug})


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
                "nimbus-ui-detail", kwargs={"slug": self.object.slug}
            )
        return response


class NimbusExperimentsCloneView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["data"] = kwargs["data"].copy()
        kwargs["data"]["owner"] = self.request.user
        return kwargs

    # TODO: https://github.com/mozilla/experimenter/issues/12432
    def get_context_data(self, **kwargs):
        return super().get_context_data(experiment=self.get_object(), **kwargs)

    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)
        if response.status_code == 302:
            response = HttpResponse()
            response.headers["HX-Redirect"] = reverse(
                "nimbus-ui-detail", kwargs={"slug": self.object.slug}
            )
        return response


class NimbusExperimentsSidebarCloneView(NimbusExperimentsCloneView):
    form_class = NimbusExperimentSidebarCloneForm
    template_name = "nimbus_experiments/clone.html"


class NimbusExperimentsPromoteToRolloutView(NimbusExperimentsCloneView):
    form_class = NimbusExperimentPromoteToRolloutForm
    template_name = "nimbus_experiments/clone.html"


class ToggleArchiveView(
    NimbusExperimentViewMixin,
    RequestFormMixin,
    RenderResponseMixin,
    UpdateView,
):
    form_class = ToggleArchiveForm
    template_name = "nimbus_experiments/archive_button.html"

    def form_valid(self, form):
        form.save()

        response = HttpResponse()
        if self.request.headers.get("HX-Request"):
            response.headers["HX-Refresh"] = "true"
        return response


class SaveAndContinueMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        if (
            self.request.headers.get("HX-Request")
            and self.request.POST.get("save_action") == "continue"
        ):
            response = HttpResponse()
            response.headers["HX-Redirect"] = reverse(
                self.continue_url_name, kwargs={"slug": self.object.slug}
            )
        return response


class OverviewUpdateView(
    SaveAndContinueMixin,
    NimbusExperimentViewMixin,
    RequestFormMixin,
    RenderResponseMixin,
    ValidationErrorsMixin,
    CloneExperimentFormMixin,
    UpdateRedirectViewMixin,
    UpdateView,
):
    form_class = OverviewForm
    template_name = "nimbus_experiments/edit_overview.html"
    continue_url_name = "nimbus-ui-update-branches"

    def can_edit(self):
        return self.object.can_edit_overview()


class DocumentationLinkCreateView(RenderParentDBResponseMixin, OverviewUpdateView):
    form_class = DocumentationLinkCreateForm


class DocumentationLinkDeleteView(RenderParentDBResponseMixin, OverviewUpdateView):
    form_class = DocumentationLinkDeleteForm


class BranchesBaseView(
    NimbusExperimentViewMixin,
    RequestFormMixin,
    ValidationErrorsMixin,
    UpdateRedirectViewMixin,
    UpdateView,
):
    form_class = NimbusBranchesForm
    template_name = "nimbus_experiments/edit_branches.html"

    def can_edit(self):
        return self.object.can_edit_branches()


class BranchesPartialUpdateView(RenderDBResponseMixin, BranchesBaseView):
    pass


class BranchesUpdateView(SaveAndContinueMixin, RenderResponseMixin, BranchesBaseView):
    continue_url_name = "nimbus-ui-update-metrics"


class BranchCreateView(RenderParentDBResponseMixin, BranchesBaseView):
    form_class = NimbusBranchCreateForm


class BranchDeleteView(RenderParentDBResponseMixin, BranchesBaseView):
    form_class = NimbusBranchDeleteForm


class BranchScreenshotCreateView(RenderParentDBResponseMixin, BranchesBaseView):
    form_class = BranchScreenshotCreateForm


class BranchScreenshotDeleteView(RenderParentDBResponseMixin, BranchesBaseView):
    form_class = BranchScreenshotDeleteForm


class MetricsUpdateView(
    SaveAndContinueMixin,
    NimbusExperimentViewMixin,
    RequestFormMixin,
    RenderResponseMixin,
    CloneExperimentFormMixin,
    ValidationErrorsMixin,
    UpdateRedirectViewMixin,
    UpdateView,
):
    form_class = MetricsForm
    template_name = "nimbus_experiments/edit_metrics.html"
    continue_url_name = "nimbus-ui-update-audience"

    def can_edit(self):
        return self.object.can_edit_metrics()


class AudienceUpdateView(
    SaveAndContinueMixin,
    NimbusExperimentViewMixin,
    RequestFormMixin,
    RenderResponseMixin,
    CloneExperimentFormMixin,
    ValidationErrorsMixin,
    UpdateRedirectViewMixin,
    UpdateView,
):
    form_class = AudienceForm
    template_name = "nimbus_experiments/edit_audience.html"
    continue_url_name = "nimbus-ui-detail"

    def can_edit(self):
        return self.object.can_edit_audience()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "custom_audiences_url": NimbusUIConstants.CUSTOM_AUDIENCES,
                "targeting_criteria_request_url": (
                    NimbusUIConstants.TARGETING_CRITERIA_REQUEST
                ),
                "targeting_criteria_request_info": (
                    NimbusUIConstants.TARGETING_CRITERIA_REQUEST_INFO
                ),
            }
        )
        return context


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


class StatusUpdateView(RequestFormMixin, RenderResponseMixin, NimbusExperimentDetailView):
    fields = None


class DraftToPreviewView(StatusUpdateView):
    form_class = DraftToPreviewForm


class PreviewToDraftView(StatusUpdateView):
    form_class = PreviewToDraftForm


class DraftToReviewView(StatusUpdateView):
    form_class = DraftToReviewForm


class PreviewToReviewView(StatusUpdateView):
    form_class = PreviewToReviewForm


class ReviewToDraftView(StatusUpdateView):
    form_class = ReviewToDraftForm


class ReviewToApproveView(StatusUpdateView):
    form_class = ReviewToApproveForm


class LiveToEndEnrollmentView(StatusUpdateView):
    form_class = LiveToEndEnrollmentForm


class ApproveEndEnrollmentView(StatusUpdateView):
    form_class = ApproveEndEnrollmentForm


class LiveToCompleteView(StatusUpdateView):
    form_class = LiveToCompleteForm


class ApproveEndExperimentView(StatusUpdateView):
    form_class = ApproveEndExperimentForm


class CancelEndEnrollmentView(StatusUpdateView):
    form_class = CancelEndEnrollmentForm


class CancelEndExperimentView(StatusUpdateView):
    form_class = CancelEndExperimentForm


class LiveToUpdateRolloutView(StatusUpdateView):
    form_class = LiveToUpdateRolloutForm


class CancelUpdateRolloutView(StatusUpdateView):
    form_class = CancelUpdateRolloutForm


class ApproveUpdateRolloutView(StatusUpdateView):
    form_class = ApproveUpdateRolloutForm


class ResultsView(NimbusExperimentViewMixin, DetailView):
    template_name = "nimbus_experiments/results.html"


class NimbusExperimentsHomeView(FilterView):
    template_name = "nimbus_experiments/home.html"
    filterset_class = NimbusExperimentFilter
    context_object_name = "experiments"

    def get_queryset(self):
        return (
            NimbusExperiment.objects.filter(is_archived=False)
            .filter(Q(owner=self.request.user) | Q(subscribers=self.request.user))
            .distinct()
            .order_by("-_updated_date_time")
            .prefetch_related("subscribers")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_experiments = list(context["experiments"])

        draft_or_preview_experiments = [
            exp for exp in all_experiments if exp.is_draft or exp.is_preview
        ]
        ready_for_attention_experiments = [
            exp for exp in all_experiments if exp.is_ready_for_attention
        ]
        draft_page = self.request.GET.get("draft_page", 1)
        attention_page = self.request.GET.get("attention_page", 1)
        my_stuff_page = self.request.GET.get("my_stuff_page", 1)
        context["draft_or_preview_page"] = Paginator(
            draft_or_preview_experiments, 5
        ).get_page(draft_page)
        context["ready_for_attention_page"] = Paginator(
            ready_for_attention_experiments, 5
        ).get_page(attention_page)
        context["all_my_experiments_page"] = Paginator(all_experiments, 25).get_page(
            my_stuff_page
        )
        context["links"] = NimbusUIConstants.HOME_PAGE_LINKS
        context["tooltips"] = NimbusUIConstants.HOME_PAGE_TOOLTIPS
        return context
