import json
from urllib.parse import urljoin

from deepdiff import DeepDiff
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView
from django.views.generic.edit import UpdateView
from django_filters.views import FilterView

from experimenter.experiments.constants import EXTERNAL_URLS, RISK_QUESTIONS
from experimenter.experiments.models import (
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusVersionedSchema,
    Tag,
)
from experimenter.nimbus_ui.constants import (
    SCHEMA_DIFF_SIZE_CONFIG,
    NimbusUIConstants,
)
from experimenter.nimbus_ui.filtersets import (
    STATUS_FILTERS,
    FeaturesPageSortChoices,
    HomeSortChoices,
    NimbusExperimentFilter,
    NimbusExperimentsHomeFilter,
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
    FeaturesForm,
    FeatureSubscribeForm,
    FeatureUnsubscribeForm,
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
    TagAssignForm,
    TagFormSet,
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

        context["live_monitor_tooltip"] = NimbusUIConstants.LIVE_MONITOR_TOOLTIP
        context["common_sidebar_links"] = NimbusUIConstants.SIDEBAR_COMMON_LINKS
        context["all_tags"] = Tag.objects.all().order_by("name")

        slug_underscore = (
            experiment.slug.replace("-", "_") if experiment and experiment.slug else ""
        )

        context["analysis_link"] = urljoin(
            NimbusUIConstants.SIDEBAR_COMMON_LINKS["Detailed Analysis"]["url"],
            slug_underscore + ".html",
        )
        context["create_form"] = NimbusExperimentCreateForm()

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


class FeatureSubscriberViewMixin(RequestFormMixin, RenderResponseMixin, UpdateView):
    """Base view for feature subscription actions."""

    model = NimbusFeatureConfig
    template_name = "nimbus_experiments/feature_subscribe_button.html"
    context_object_name = "feature_config_slug"
    url_name = None

    def get_success_url(self):
        return reverse(self.url_name, kwargs={"slug": self.object.slug})


class NimbusChangeLogsView(
    NimbusExperimentViewMixin, CloneExperimentFormMixin, DetailView
):
    template_name = "changelog/overview.html"


class NimbusExperimentsListView(NimbusExperimentViewMixin, FilterView):
    queryset = (
        NimbusExperiment.objects.with_merged_channel()
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
        (
            outcome,
            f"{outcome_doc_base_url}{experiment.application.replace('-', '_')}/{outcome}",
        )
        for outcome in experiment.primary_outcomes
    ]
    secondary_outcome_links = [
        (
            outcome,
            f"{outcome_doc_base_url}{experiment.application.replace('-', '_')}/{outcome}",
        )
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["links"] = NimbusUIConstants.OVERVIEW_PAGE_LINKS
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["links"] = NimbusUIConstants.METRICS_PAGE_LINKS
        return context


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
                "targeting_criteria_request_info": (
                    NimbusUIConstants.TARGETING_CRITERIA_REQUEST_INFO
                ),
                "links": NimbusUIConstants.AUDIENCE_PAGE_LINKS,
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


class FeatureSubscribeView(FeatureSubscriberViewMixin):
    form_class = FeatureSubscribeForm
    url_name = "nimbus-ui-feature-subscribe"


class FeatureUnsubscribeView(FeatureSubscriberViewMixin):
    form_class = FeatureUnsubscribeForm
    url_name = "nimbus-ui-feature-unsubscribe"


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


class NewResultsView(NimbusExperimentViewMixin, DetailView):
    template_name = "nimbus_experiments/results-new.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment = self.get_object()

        analysis_data = experiment.results_data.get("v3", {})

        context["default_metrics"] = experiment.default_metrics

        selected_reference_branch = self.request.GET.get(
            "reference_branch", experiment.reference_branch.slug
        )
        context["selected_reference_branch"] = selected_reference_branch

        selected_segment = self.request.GET.get("segment", "all")
        context["selected_segment"] = selected_segment

        analysis_basis = self.request.GET.get(
            "analysis_basis", "exposures" if experiment.has_exposures else "enrollments"
        )
        context["selected_analysis_basis"] = analysis_basis

        context["results_data"] = analysis_data
        context["overview_sections"] = NimbusUIConstants.OVERVIEW_SECTIONS
        context["overview_section_tooltips"] = (
            NimbusUIConstants.OVERVIEW_REFLECTION_PROMPTS
        )

        context["branch_data"] = experiment.get_branch_data(
            analysis_basis, selected_segment
        )

        return context


class ResultsView(NimbusExperimentViewMixin, DetailView):
    template_name = "nimbus_experiments/results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NimbusFeaturesView(TemplateView):
    template_name = "nimbus_experiments/features.html"
    form_class = FeaturesForm
    filterset_class = NimbusExperimentFilter
    context_object_name = "features"

    def get_form(self):
        return FeaturesForm(self.request.GET or None)

    def get_queryset(self):
        qs = (
            NimbusExperiment.objects.with_merged_channel()
            .filter(is_archived=False)
            .order_by("-_updated_date_time")
        )

        app = self.request.GET.get("application")
        if app:
            qs = qs.filter(application=app)

        feature_id = self.request.GET.get("feature_configs")
        if feature_id:
            sort_param = self.request.GET.get("sort", "name")
            if sort_param in [
                "change_version",
                "-change_version",
                "change_size",
                "-change_size",
            ]:
                sort_param = "name"

            qs = qs.filter(feature_configs=feature_id).distinct().order_by(sort_param)
        else:
            return qs.none()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        qs = self.get_queryset()
        schemas_with_changes = 0
        feature_config_slug = None

        deliveries_paginator = Paginator(qs, 5)
        deliveries_page_number = self.request.GET.get("deliveries_page") or 1
        deliveries_page_obj = deliveries_paginator.get_page(deliveries_page_number)

        experiments_with_qa_status = qs.exclude(
            qa_status=NimbusExperiment.QAStatus.NOT_SET.value
        )

        qa_runs_paginator = Paginator(experiments_with_qa_status, 5)
        qa_runs_page_number = self.request.GET.get("qa_runs") or 1
        qa_runs_page_obj = qa_runs_paginator.get_page(qa_runs_page_number)

        # header fields for the deliveries table
        deliveries_sortable_headers = FeaturesPageSortChoices.sortable_headers(
            FeaturesPageSortChoices.Deliveries
        )
        deliveries_non_sortable_headers = [("delivery_brief", "Delivery Brief")]
        deliveries_sortable_header = (
            deliveries_sortable_headers + deliveries_non_sortable_headers
        )
        deliveries_non_sortable_fields = {
            field for field, _ in deliveries_non_sortable_headers
        }

        # header fields for the qa runs table
        qa_runs_sortable_headers = FeaturesPageSortChoices.sortable_headers(
            FeaturesPageSortChoices.QARuns
        )
        qa_runs_non_sortable_headers = [
            ("qa_run", "QA Run"),
            ("qa_status", "QA Status"),
            ("qa_test_plan", "Test Plan/Recipe"),
            ("qa_testrail_link", "TestRail Results"),
        ]
        qa_runs_sortable_header = (
            qa_runs_non_sortable_headers[:1]
            + qa_runs_sortable_headers
            + qa_runs_non_sortable_headers[1:]
        )
        qa_runs_non_sortable_fields = {field for field, _ in qa_runs_non_sortable_headers}

        feature_changes_sortable_headers = FeaturesPageSortChoices.sortable_headers(
            FeaturesPageSortChoices.FeatureChanges
        )
        feature_changes_non_sortable_headers = [
            ("show_diff", "Change Diff from Prev. (Previous | Current)")
        ]

        feature_change_headers = (
            feature_changes_sortable_headers + feature_changes_non_sortable_headers
        )

        # Get feature schema versions with their diffs
        feature_schemas = []
        feature_id = self.request.GET.get("feature_configs")
        thresholds = SCHEMA_DIFF_SIZE_CONFIG["thresholds"]
        labels = SCHEMA_DIFF_SIZE_CONFIG["labels"]
        total_changes = 0

        if feature_id:
            sort = self.request.GET.get("sort", "")

            if sort == "change_version":
                queryset = NimbusVersionedSchema.objects.with_version_ordering(
                    descending=False
                )
            else:
                queryset = NimbusVersionedSchema.objects.with_version_ordering(
                    descending=True
                )

            schemas = list(
                queryset.filter(feature_config_id=feature_id).select_related("version")
            )

            schema_cache = []
            for schema in schemas:
                schema_cache.append(json.loads(schema.schema))

            # Pair each schema with its previous version
            for i, schema in enumerate(schemas):
                current_json = schema.schema
                previous_json = schemas[i + 1].schema if i + 1 < len(schemas) else '"{}"'

                if i + 1 < len(schemas):
                    diff = DeepDiff(
                        schema_cache[i + 1],
                        schema_cache[i],
                        ignore_order=True,
                    )

                    total_changes = sum(
                        [
                            len(diff.get("dictionary_item_added", [])),
                            len(diff.get("dictionary_item_removed", [])),
                            len(diff.get("values_changed", {})),
                            len(diff.get("type_changes", {})),
                        ]
                    )

                    if total_changes == 0:
                        size_label = labels["no_changes"]
                    elif total_changes <= thresholds["small"]:
                        size_label = labels["small"]
                    elif total_changes <= thresholds["medium"]:
                        size_label = labels["medium"]
                    else:
                        size_label = labels["large"]

                    if total_changes > 0:
                        schemas_with_changes += 1
                else:
                    total_changes = 0
                    size_label = labels["first_version"]

                feature_schemas.append(
                    {
                        "schema": schema,
                        "current_json": current_json,
                        "previous_json": previous_json,
                        "size_label": size_label.get("text"),
                        "size_badge": size_label.get("badge_class"),
                        "total_changes": total_changes,
                    }
                )

            if sort == "change_size":
                feature_schemas.sort(key=lambda x: x["total_changes"])
            elif sort == "-change_size":
                feature_schemas.sort(key=lambda x: x["total_changes"], reverse=True)

        feature_changes_pagination = Paginator(feature_schemas, 5)
        feature_changes_page_number = self.request.GET.get("feature_changes") or 1
        feature_changes_page_obj = feature_changes_pagination.get_page(
            feature_changes_page_number
        )
        if feature_id:
            feature_config_slug = NimbusFeatureConfig.objects.get(pk=feature_id)

        context = {
            "form": form,
            "links": NimbusUIConstants.FEATURE_PAGE_LINKS,
            "tooltips": NimbusUIConstants.FEATURE_PAGE_TOOLTIPS,
            "application": self.request.GET.get("application"),
            "feature_configs": self.request.GET.get("feature_configs"),
            "feature_config_slug": feature_config_slug,
            "paginator": deliveries_paginator,
            "deliveries_page_obj": deliveries_page_obj,
            "experiments_delivered": deliveries_page_obj.object_list,
            "qa_runs_page_obj": qa_runs_page_obj,
            "experiments_with_qa_status": qa_runs_page_obj.object_list,
            "deliveries_sortable_header": deliveries_sortable_header,
            "deliveries_non_sortable_header": deliveries_non_sortable_fields,
            "qa_runs_sortable_header": qa_runs_sortable_header,
            "qa_runs_non_sortable_header": qa_runs_non_sortable_fields,
            "feature_schemas": feature_changes_page_obj.object_list,
            "feature_changes_page_obj": feature_changes_page_obj,
            "schemas_with_changes": schemas_with_changes,
            "feature_changes_headers": feature_change_headers,
            "feature_changes_non_sortable_headers": feature_changes_non_sortable_headers,
        }
        return context


class NimbusExperimentsHomeView(FilterView):
    template_name = "nimbus_experiments/home.html"
    filterset_class = NimbusExperimentsHomeFilter
    context_object_name = "experiments"

    def get_queryset(self):
        subscribed_features = NimbusFeatureConfig.objects.filter(
            subscribers=self.request.user
        )

        return (
            NimbusExperiment.objects.with_merged_channel()
            .filter(is_archived=False)
            .filter(
                Q(owner=self.request.user)
                | Q(subscribers=self.request.user)
                | Q(feature_configs__in=subscribed_features)
            )
            .distinct()
            .order_by("-_updated_date_time")
            .prefetch_related("subscribers")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = self.get_queryset()

        # Used for filtering + pagination
        home_filter = NimbusExperimentsHomeFilter(
            data=self.request.GET,
            request=self.request,
            queryset=base_qs,
        )
        context["my_deliveries_filter"] = home_filter

        my_deliveries_page = self.request.GET.get("my_deliveries_page", 1)
        context["all_my_experiments_page"] = Paginator(home_filter.qs, 25).get_page(
            my_deliveries_page
        )

        all_experiments = list(base_qs)
        context["draft_or_preview_page"] = Paginator(
            [e for e in all_experiments if e.is_draft or e.is_preview], 5
        ).get_page(self.request.GET.get("draft_page", 1))
        context["ready_for_attention_page"] = Paginator(
            [e for e in all_experiments if e.is_ready_for_attention], 5
        ).get_page(self.request.GET.get("attention_page", 1))

        context["links"] = NimbusUIConstants.HOME_PAGE_LINKS
        context["tooltips"] = NimbusUIConstants.HOME_PAGE_TOOLTIPS

        context["sortable_headers"] = HomeSortChoices.sortable_headers()
        context["create_form"] = NimbusExperimentCreateForm()
        return context


class TagFormSetMixin:
    def get_tag_formset(self, data=None):
        queryset = Tag.objects.all().order_by("id")
        return TagFormSet(data, queryset=queryset)


class TagsManageView(TagFormSetMixin, TemplateView):
    template_name = "nimbus_experiments/tags_manage.html"

    def get_context_data(self, **kwargs):
        return {"formset": self.get_tag_formset()}


class TagCreateView(TagFormSetMixin, TemplateView):
    template_name = "nimbus_experiments/tags_list_partial.html"

    def post(self, request, *args, **kwargs):
        formset = self.get_tag_formset()
        formset.create_tag()
        return render(
            request,
            self.template_name,
            {"formset": self.get_tag_formset()},
        )


class TagSaveView(TagFormSetMixin, TemplateView):
    template_name = "nimbus_experiments/tags_list_partial.html"

    def post(self, request, *args, **kwargs):
        formset = self.get_tag_formset(request.POST)
        if formset.is_valid():
            formset.save()
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Refresh"] = "true"
            return response
        return render(request, self.template_name, {"formset": formset})


class TagAssignView(NimbusExperimentViewMixin, RenderResponseMixin, UpdateView):
    form_class = TagAssignForm
    template_name = "nimbus_experiments/assign_tags_response.html"
