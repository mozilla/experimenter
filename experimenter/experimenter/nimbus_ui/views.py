import json

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
    METRICS_MIN_BOUNDS_WIDTH,
    SCHEMA_DIFF_SIZE_CONFIG,
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
    BranchLeadingScreenshotForm,
    BranchScreenshotCreateForm,
    BranchScreenshotDeleteForm,
    CancelEndEnrollmentForm,
    CancelEndExperimentForm,
    CancelUpdateRolloutForm,
    CollaboratorsForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    DraftToPreviewForm,
    DraftToReviewForm,
    EditOutcomeSummaryForm,
    FeaturesForm,
    FeatureSubscribersForm,
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
    ToggleReviewSlackNotificationsForm,
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
        context["all_tags"] = Tag.objects.all().order_by("name")
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
        context["collaborators_form"] = CollaboratorsForm(instance=self.object)

        if "save_failed" in self.request.GET:
            context["save_failed"] = True

        return context


class QAStatusUpdateView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    form_class = QAStatusForm
    template_name = "nimbus_experiments/qa_edit_form.html"

    def form_valid(self, form):
        super().form_valid(form)
        return render(
            self.request,
            "nimbus_experiments/qa_card.html",
            {"experiment": self.object, "container_only": True, "update_header": True},
        )


class TakeawaysUpdateView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    form_class = TakeawaysForm
    template_name = "nimbus_experiments/takeaways_edit_form.html"

    def form_valid(self, form):
        super().form_valid(form)
        return render(
            self.request,
            "nimbus_experiments/takeaways_card.html",
            {"experiment": self.object},
        )


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


class CollaboratorsContextMixin:
    template_name = "nimbus_experiments/subscribers_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collaborators_form"] = CollaboratorsForm(instance=self.object)
        return context


class CollaboratorsUpdateView(
    CollaboratorsContextMixin,
    NimbusExperimentViewMixin,
    RequestFormMixin,
    RenderResponseMixin,
    UpdateView,
):
    form_class = CollaboratorsForm


class SubscribeView(
    CollaboratorsContextMixin,
    NimbusExperimentViewMixin,
    RequestFormMixin,
    RenderResponseMixin,
    UpdateView,
):
    form_class = SubscribeForm


class UnsubscribeView(
    CollaboratorsContextMixin,
    NimbusExperimentViewMixin,
    RequestFormMixin,
    RenderResponseMixin,
    UpdateView,
):
    form_class = UnsubscribeForm


class ToggleReviewSlackNotificationsView(
    NimbusExperimentViewMixin,
    RequestFormMixin,
    UpdateView,
):
    form_class = ToggleReviewSlackNotificationsForm

    def get_success_url(self):
        return reverse("nimbus-ui-detail", kwargs={"slug": self.object.slug})


class FeatureSubscribersUpdateView(
    RequestFormMixin,
    RenderResponseMixin,
    UpdateView,
):
    model = NimbusFeatureConfig
    form_class = FeatureSubscribersForm
    template_name = "nimbus_experiments/feature_subscribers.html"
    context_object_name = "selected_feature_config"

    def get_success_url(self):
        return reverse(
            "nimbus-ui-feature-update-subscribers", kwargs={"pk": self.object.pk}
        )


class StatusUpdateView(RequestFormMixin, RenderResponseMixin, NimbusExperimentDetailView):
    fields = None

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            fragment = self.request.GET.get("fragment") or self.request.POST.get(
                "fragment"
            )

            if fragment == "progress_card":
                return ["nimbus_experiments/launch_controls_v2.html"]

        return [self.template_name]

    def get_context_data(self, *, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.request.method in ("POST", "PUT") and form and not form.is_valid():
            context["update_status_form_errors"] = form.errors["__all__"]

        return context


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


class EditOutcomeSummaryView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    form_class = EditOutcomeSummaryForm
    template_name = "common/edit_outcome_summary_form.html"

    def form_valid(self, form):
        super().form_valid(form)
        response = HttpResponse()
        response.headers["HX-Refresh"] = "true"
        return response


class BranchLeadingScreenshotView(
    NimbusExperimentViewMixin,
    RequestFormMixin,
    UpdateView,
):
    form_class = BranchLeadingScreenshotForm

    def get_branch(self):
        return (
            self.get_object().branches.filter(slug=self.kwargs.get("branch_slug")).first()
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if branch := self.get_branch():
            if screenshot := branch.screenshots.first():
                kwargs["instance"] = screenshot
            else:
                # create an unsaved placeholder instance of the correct model
                screenshot_model = branch.screenshots.model
                kwargs["instance"] = screenshot_model(branch=branch)

        return kwargs

    def form_valid(self, form):
        form.save()
        response = HttpResponse()
        response.headers["HX-Refresh"] = "true"
        return response


class NewResultsView(NimbusExperimentViewMixin, DetailView):
    template_name = "nimbus_experiments/results-new.html"

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["nimbus_experiments/results-new-fragment.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment = self.get_object()

        analysis_data = experiment.results_data.get("v3", {})

        selected_reference_branch = self.request.GET.get(
            "reference_branch", experiment.reference_branch.slug
        )
        context["selected_reference_branch"] = selected_reference_branch

        segments = list(analysis_data.get("overall", {}).get("enrollments", {}).keys())
        selected_segment = self.request.GET.get("segment", "all")
        context["selected_segment"] = selected_segment
        context["segments"] = segments

        analysis_basis = self.request.GET.get(
            "analysis_basis", "exposures" if experiment.has_exposures else "enrollments"
        )
        context["selected_analysis_basis"] = analysis_basis

        context["branch_data"] = experiment.get_branch_data(
            analysis_basis, selected_segment
        )

        context["metric_area_data"] = experiment.get_metric_data(
            analysis_basis, selected_segment, selected_reference_branch
        )

        context["edit_outcome_summary_form"] = EditOutcomeSummaryForm(instance=experiment)

        branch_leading_screenshot_forms = {
            branch.slug: BranchLeadingScreenshotForm(instance=branch.screenshots.first())
            for branch in experiment.branches.all()
        }
        context["branch_leading_screenshot_forms"] = branch_leading_screenshot_forms

        all_metrics = experiment.get_metric_data(
            analysis_basis, selected_segment, selected_reference_branch
        )
        context["metric_area_data"] = all_metrics

        relative_metric_changes = {}

        for metric_data in all_metrics.values():
            metadata = metric_data.get("metrics", {})

            # Prepare relative metric changes for UI rendering
            for metric_metadata in metadata:
                data = (
                    metric_data.get("data", {})
                    .get("overall", {})
                    .get(metric_metadata["slug"], {})
                )
                metric_ui_properties = {}
                extreme_bound = experiment.get_max_metric_value(
                    analysis_basis,
                    selected_segment,
                    selected_reference_branch,
                    metric_metadata["group"],
                    metric_metadata["slug"],
                )

                for branch_slug, branch_data in data.items():
                    if not (relative := branch_data.get("relative")):
                        continue

                    lower = relative[0].get("lower") * 100
                    upper = relative[0].get("upper") * 100
                    confidence_range = round(extreme_bound * 1000) / 10
                    full_width = confidence_range * 2
                    bar_width = ((upper - lower) / full_width) * 100
                    left_percent = (abs(lower - confidence_range * -1) / full_width) * 100
                    left_bounds_percent = left_percent

                    num_digits = len(str(round(lower, 1)).replace(".", "")) + len(
                        str(round(upper, 1)).replace(".", "")
                    )

                    if bar_width < METRICS_MIN_BOUNDS_WIDTH:
                        left_bounds_percent -= (METRICS_MIN_BOUNDS_WIDTH - bar_width) / 2

                    metric_ui_properties[branch_slug] = {
                        "bar_width": bar_width,
                        "left_percent": left_percent,
                        "left_bounds_percent": left_bounds_percent - num_digits * 1.5,
                        "bounds_width": (
                            max(bar_width, METRICS_MIN_BOUNDS_WIDTH) + num_digits * 3
                        ),
                    }

                    relative_metric_changes[metric_metadata["slug"]] = (
                        metric_ui_properties
                    )

        context["relative_metric_changes"] = relative_metric_changes
        context["all_weekly_metric_data"] = experiment.get_weekly_metric_data(
            analysis_basis, selected_segment, selected_reference_branch
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

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.app = self.request.GET.get("application")
        self.feature_id = self.request.GET.get("feature_configs")

    def get_form(self):
        return FeaturesForm(self.request.GET or None)

    def get_queryset(self):
        if not self.app or not self.feature_id:
            return NimbusExperiment.objects.none()

        qs = (
            NimbusExperiment.objects.with_merged_channel()
            .filter(is_archived=False, application=self.app)
            .order_by("-_updated_date_time")
        )

        sort_param = self.request.GET.get("sort", "name")
        if sort_param in [
            "change_version",
            "-change_version",
            "change_size",
            "-change_size",
        ]:
            sort_param = "name"

        qs = qs.filter(feature_configs=self.feature_id).distinct().order_by(sort_param)

        return qs

    def get_feature_config(self):
        if not self.feature_id or not self.app:
            return None

        return (
            NimbusFeatureConfig.objects.filter(pk=self.feature_id, application=self.app)
            .prefetch_related("subscribers")
            .first()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        qs = self.get_queryset()
        schemas_with_changes = 0
        selected_feature_config = self.get_feature_config()

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
        thresholds = SCHEMA_DIFF_SIZE_CONFIG["thresholds"]
        labels = SCHEMA_DIFF_SIZE_CONFIG["labels"]
        total_changes = 0

        if selected_feature_config:
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
                queryset.filter(feature_config_id=self.feature_id).select_related(
                    "version"
                )
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

        context = {
            "form": form,
            "application": self.request.GET.get("application"),
            "feature_configs": self.request.GET.get("feature_configs"),
            "selected_feature_config": selected_feature_config,
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

        # Add subscribers form if a feature is selected
        if selected_feature_config:
            context["subscribers_form"] = FeatureSubscribersForm(
                instance=selected_feature_config
            )

        return context


class NimbusExperimentsHomeView(FilterView):
    template_name = "nimbus_experiments/home.html"
    filterset_class = NimbusExperimentsHomeFilter
    context_object_name = "experiments"

    def get_queryset(self):
        return (
            NimbusExperiment.objects.with_merged_channel()
            .filter(is_archived=False)
            .filter(
                Q(owner=self.request.user)
                | Q(subscribers=self.request.user)
                | Q(feature_configs__subscribers=self.request.user)
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


class TagAssignView(
    NimbusExperimentViewMixin, RequestFormMixin, RenderResponseMixin, UpdateView
):
    form_class = TagAssignForm
    template_name = "nimbus_experiments/assign_tags_response.html"
