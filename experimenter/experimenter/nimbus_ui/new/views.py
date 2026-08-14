from django import forms
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from experimenter.experiments.api.v5.serializers import NimbusRolloutReviewSerializer
from experimenter.experiments.constants import EXTERNAL_URLS, RISK_QUESTIONS
from experimenter.experiments.models import NimbusExperiment, Tag
from experimenter.nimbus_ui.filtersets import (
    TagSearchFilterSet,
    UserSearchFilterSet,
)
from experimenter.nimbus_ui.forms import ToggleArchiveForm
from experimenter.nimbus_ui.new.forms import (
    AdvancePhaseReviewApproveRolloutForm,
    AdvancePhaseReviewRejectRolloutForm,
    AdvancePhaseReviewRolloutForm,
    CollaboratorsForm,
    DisabledToLiveDuplicatePhaseReviewRolloutForm,
    DisabledToLiveReviewApproveRolloutForm,
    DisabledToLiveReviewRejectRolloutForm,
    DisabledToLiveReviewRolloutForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    DraftReviewApproveRolloutForm,
    DraftReviewRejectForm,
    DraftReviewRolloutForm,
    DraftToPreviewRolloutForm,
    LiveToDisabledReviewApproveRolloutForm,
    LiveToDisabledReviewRejectRolloutForm,
    LiveToDisabledReviewRolloutForm,
    NimbusExperimentCreateForm,
    NimbusExperimentSidebarCloneForm,
    PreviewReviewRolloutForm,
    PreviewToDraftRolloutForm,
    RolloutAudienceForm,
    RolloutFeaturesForm,
    RolloutOverviewForm,
    RolloutPhaseCreateForm,
    RolloutPhaseDeleteForm,
    RolloutPlanApplyForm,
    RolloutPlanCreateForm,
    RolloutQAStatusForm,
    RolloutRisksForm,
    RolloutScheduleForm,
    RolloutScreenshotCreateForm,
    RolloutScreenshotDeleteForm,
    RolloutSignoffForm,
    SubscribeForm,
    TagAssignForm,
    ToggleReviewSlackNotificationsForm,
    UnsubscribeForm,
)


class CloneExperimentFormMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clone_form"] = NimbusExperimentSidebarCloneForm(instance=self.object)
        return context


class RequestFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class PrefetchExperimentQuerysetMixin:
    def get_queryset(self):
        if self.request.method in ("GET", "HEAD"):
            return NimbusExperiment.objects.with_related()
        return super().get_queryset()


class RenderResponseMixin:
    def form_valid(self, form):
        super().form_valid(form)
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

        if experiment and experiment.slug:
            context["slack_notifications_form"] = ToggleReviewSlackNotificationsForm(
                instance=experiment
            )

        return context


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
            (
                f"{segment_doc_base_url}"
                f"{experiment.application.replace('-', '_')}/"
                f"#{segment}"
            ),
        )
        for segment in experiment.segments
    ]
    context = {
        "RISK_QUESTIONS": RISK_QUESTIONS,
        "EXTERNAL_URLS": EXTERNAL_URLS,
        "primary_outcome_links": primary_outcome_links,
        "secondary_outcome_links": secondary_outcome_links,
        "segment_links": segment_links,
        "uses_secure_collection": (
            experiment.kinto_collection == settings.KINTO_COLLECTION_NIMBUS_SECURE
        ),
    }
    return context


class NimbusExperimentDetailView(
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

        return context


class RenderParentDBResponseMixin:
    def form_valid(self, form):
        super().form_valid(form)
        form = super().form_class(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form))


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


class RolloutSetupProgressMixin:
    SETUP_SECTIONS = {
        "Overview": {
            "card_id": "overview",
            "fields": {*RolloutOverviewForm.Meta.fields},
        },
        "Risks": {
            "card_id": "risks",
            "fields": {*RolloutRisksForm.Meta.fields},
        },
        "Features": {
            "card_id": "rollout-features",
            "fields": {*RolloutFeaturesForm.Meta.fields},
        },
        "Audience": {
            "card_id": "audience",
            "fields": {*RolloutAudienceForm.Meta.fields},
        },
        "Rollout schedule": {
            "card_id": "schedule",
            "fields": {"rollout_phases"},
            "labels": {"rollout_phases": "Rollout Schedule"},
        },
    }

    def flatten_errors(self, messages):
        if isinstance(messages, dict):
            return [m for value in messages.values() for m in self.flatten_errors(value)]
        if isinstance(messages, (list, tuple)):
            return [m for value in messages for m in self.flatten_errors(value)]
        return [str(messages)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        field_errors = self.object.get_invalid_fields_errors(
            serializer_class=NimbusRolloutReviewSerializer
        )
        validation_errors = {
            field: self.flatten_errors(messages)
            for field, messages in field_errors.items()
        }
        error_keys = set(field_errors)

        field_to_section = {
            field: name
            for name, section in self.SETUP_SECTIONS.items()
            for field in section["fields"]
        }

        tracked_fields = set(field_to_section)
        broken = error_keys & tracked_fields
        context["setup_completion_percent"] = round(
            100 * (len(tracked_fields) - len(broken)) / len(tracked_fields)
        )

        issues = []
        for field, messages in field_errors.items():
            section = field_to_section.get(field)
            if section is not None:
                meta = self.SETUP_SECTIONS[section]
                card_id = meta["card_id"]
                label = meta.get("labels", {}).get(field, field.replace("_", " ").title())
            else:
                section = "Other"
                card_id = None
                label = field.replace("_", " ").title()
            issues.append(
                {
                    "section": section,
                    "card_id": card_id,
                    "label": label,
                    "messages": self.flatten_errors(messages),
                }
            )

        context["setup_issues"] = issues
        context["setup_issues_count"] = len(issues)
        context["validation_errors"] = validation_errors
        return context


class NimbusRolloutDetailView(
    PrefetchExperimentQuerysetMixin,
    RolloutSetupProgressMixin,
    NimbusExperimentViewMixin,
    CloneExperimentFormMixin,
    DetailView,
):
    template_name = "new/rollouts/rollout_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_experiment_context(self.object))
        return context

    def get_queryset(self):
        return super().get_queryset().filter(is_rollout=True)


class CardMixin:
    form_class: type[forms.ModelForm]
    template_name = None
    cancel_url_name = "new-nimbus-ui-rollout-detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not isinstance(kwargs.get("form"), self.form_class):
            context["form"] = self.form_class(instance=self.object)
        context["cancel_url"] = reverse(
            self.cancel_url_name, kwargs={"slug": self.object.slug}
        )
        return context


class NewCardUpdateView(
    PrefetchExperimentQuerysetMixin,
    RolloutSetupProgressMixin,
    NimbusExperimentViewMixin,
    RequestFormMixin,
    UpdateRedirectViewMixin,
    UpdateView,
):
    display_template = None

    def can_edit(self):
        return self.object.can_edit_overview()

    def form_valid(self, form):
        self.object = form.save()
        return self.render_valid_response()

    def render_valid_response(self):
        context = self.get_context_data()
        context["hx_swap_oob"] = True
        return self.response_class(
            request=self.request,
            template=self.display_template,
            context=context,
        )


class NewOverviewUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutOverviewForm
    display_template = "new/rollouts/overview/card.html"
    template_name = "new/rollouts/overview/edit_form.html"


class NewOverviewCancelView(NimbusRolloutDetailView):
    def post(self, request, *args, **kwargs):
        self.get_object().documentation_links.filter(link="").delete()
        return self.get(request, *args, **kwargs)


class NewRisksUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutRisksForm
    display_template = "new/rollouts/risks/card.html"
    template_name = "new/rollouts/risks/edit_form.html"


class NewAudienceUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutAudienceForm
    display_template = "new/rollouts/audience/card.html"
    template_name = "new/rollouts/audience/edit_form.html"

    def render_valid_response(self):
        self.object.refresh_from_db()

        if "save" in self.request.POST:
            return super().render_valid_response()

        return self.render_to_response(self.get_context_data())


class NewRolloutFeaturesUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutFeaturesForm
    display_template = "new/rollouts/rollout_features/card.html"
    template_name = "new/rollouts/rollout_features/edit_form.html"
    save_without_explicit_submit = False

    def form_valid(self, form):
        # If the request came from the explicit Save button, return the read-only card
        # view so the UI swaps back to the card. When the form is posted for intermediate
        # updates (e.g. feature_configs changed via hx-post on change), return the
        # editable form so the user can continue editing.

        if "save" in self.request.POST or self.save_without_explicit_submit:
            return super().form_valid(form)

        return self.render_to_response(self.get_context_data(form=form))


class NewRolloutScreenshotCreateView(
    RenderParentDBResponseMixin, NewRolloutFeaturesUpdateView
):
    form_class = RolloutScreenshotCreateForm
    save_without_explicit_submit = True


class NewRolloutScreenshotUploadView(
    RenderParentDBResponseMixin, NewRolloutFeaturesUpdateView
):
    form_class = RolloutFeaturesForm
    save_without_explicit_submit = True


class NewRolloutScreenshotDeleteView(
    RenderParentDBResponseMixin, NewRolloutFeaturesUpdateView
):
    form_class = RolloutScreenshotDeleteForm
    save_without_explicit_submit = True


class NewQAUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutQAStatusForm
    display_template = "new/rollouts/qa/card.html"
    template_name = "new/rollouts/qa/edit_form.html"

    def can_edit(self):
        return True


class NewSignoffUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutSignoffForm
    display_template = "new/rollouts/signoff/card.html"
    template_name = "new/rollouts/signoff/edit_form.html"

    def can_edit(self):
        return True


class CardMutationMixin:
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_edit():
            response = HttpResponse()
            base_url = reverse("nimbus-ui-detail", kwargs={"slug": self.object.slug})
            response.headers["HX-Redirect"] = f"{base_url}?save_failed=true"
            return response

        form = self.get_form()
        if form.is_valid():
            form.save()
        else:
            self.mutate(form)

        form = super().form_class(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form))

    def mutate(self, form):
        raise NotImplementedError


class NewDocumentationLinkCreateView(RenderParentDBResponseMixin, NewOverviewUpdateView):
    form_class = DocumentationLinkCreateForm


class NewDocumentationLinkDeleteView(CardMutationMixin, NewOverviewUpdateView):
    form_class = DocumentationLinkDeleteForm

    def mutate(self, form):
        link_id = self.request.POST.get("link_id")
        self.object.documentation_links.filter(id=link_id).delete()


class NewM2MSearchView(NimbusExperimentViewMixin, DetailView):
    """Base for search-as-you-type views that find items not yet assigned to an
    experiment M2M relation.

    Subclasses must define:
      m2m_attr        - experiment attribute to read already-assigned IDs from
      context_key     - template variable name for the results list
      filterset_class - FilterSet used to filter the queryset
      ordering        - field name to order results by
      require_query   - if True, return empty queryset when no query is provided
    """

    m2m_attr = None
    context_key = None
    filterset_class: type
    ordering = None
    require_query = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        excluded_ids = getattr(self.object, self.m2m_attr).values_list("id", flat=True)
        if self.require_query and not q:
            context[self.context_key] = self.filterset_class.Meta.model.objects.none()
            return context
        base_qs = self.filterset_class.Meta.model.objects.exclude(id__in=excluded_ids)
        fs = self.filterset_class(self.request.GET, queryset=base_qs)
        qs = fs.qs.order_by(self.ordering) if self.ordering else fs.qs
        context[self.context_key] = qs[:15]
        return context


class NewTagSearchView(NewM2MSearchView):
    template_name = "new/rollouts/overview/tag_search_results.html"
    m2m_attr = "tags"
    context_key = "tags"
    filterset_class = TagSearchFilterSet
    ordering = "name"


class NewM2MDeltaMixin:
    """Handles per-item add/remove for an M2M field, injecting the full new set
    into the form so the existing batch form classes work unchanged."""

    item_id_key = None  # POST key for the item being toggled
    m2m_attr = None  # attribute on experiment (e.g. "tags", "subscribers")
    form_field = None  # form field name (e.g. "tags", "collaborators")
    add = True  # True = add item, False = remove item

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        item_id = self.request.POST.get(self.item_id_key)
        if item_id:
            current_ids = set(
                getattr(self.object, self.m2m_attr).values_list("id", flat=True)
            )
            item_id = int(item_id)
            new_ids = current_ids | {item_id} if self.add else current_ids - {item_id}
            data = self.request.POST.copy()
            data.setlist(self.form_field, [str(i) for i in new_ids])
            kwargs["data"] = data
        return kwargs


class NewOverviewFieldUpdateView(NewCardUpdateView):
    field_template = None

    def form_valid(self, form):
        self.object = form.save()
        return self.response_class(
            request=self.request,
            template=self.field_template,
            context=self.get_context_data(),
        )


class NewTagView(NewM2MDeltaMixin, CardMixin, NewOverviewFieldUpdateView):
    item_id_key = "tag_id"
    m2m_attr = "tags"
    form_field = "tags"
    form_class = TagAssignForm
    template_name = "new/rollouts/overview/edit_form.html"
    field_template = "new/rollouts/overview/tags_field.html"


class NewAddTagView(NewTagView):
    add = True


class NewRemoveTagView(NewTagView):
    add = False


class NewSubscriberSearchView(NewM2MSearchView):
    template_name = "new/rollouts/overview/subscriber_search_results.html"
    m2m_attr = "subscribers"
    context_key = "users"
    filterset_class = UserSearchFilterSet
    ordering = "email"
    require_query = True


class NewSubscriberView(NewM2MDeltaMixin, CardMixin, NewOverviewFieldUpdateView):
    item_id_key = "user_id"
    m2m_attr = "subscribers"
    form_field = "collaborators"
    form_class = CollaboratorsForm
    template_name = "new/rollouts/overview/edit_form.html"
    field_template = "new/rollouts/overview/subscribers_field.html"


class NewAddSubscriberView(NewSubscriberView):
    add = True


class NewRemoveSubscriberView(NewSubscriberView):
    add = False


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

    def form_valid(self, form):
        if self.request.headers.get("HX-Request"):
            form.save()
            response = HttpResponse()
            response.headers["HX-Refresh"] = "true"
            return response

        return super().form_valid(form)


class DraftToPreviewRolloutView(StatusUpdateView):
    form_class = DraftToPreviewRolloutForm


class DraftReviewRolloutView(StatusUpdateView):
    form_class = DraftReviewRolloutForm


class DraftReviewApproveRolloutView(StatusUpdateView):
    form_class = DraftReviewApproveRolloutForm


class DraftReviewRejectView(StatusUpdateView):
    form_class = DraftReviewRejectForm


class PreviewReviewRolloutView(StatusUpdateView):
    form_class = PreviewReviewRolloutForm


class PreviewToDraftRolloutView(StatusUpdateView):
    form_class = PreviewToDraftRolloutForm


class AdvancePhaseReviewRolloutView(StatusUpdateView):
    form_class = AdvancePhaseReviewRolloutForm


class AdvancePhaseReviewApproveRolloutView(StatusUpdateView):
    form_class = AdvancePhaseReviewApproveRolloutForm


class AdvancePhaseReviewRejectRolloutView(StatusUpdateView):
    form_class = AdvancePhaseReviewRejectRolloutForm


class LiveToDisabledReviewRolloutView(StatusUpdateView):
    form_class = LiveToDisabledReviewRolloutForm


class LiveToDisabledReviewApproveRolloutView(StatusUpdateView):
    form_class = LiveToDisabledReviewApproveRolloutForm


class LiveToDisabledReviewRejectRolloutView(StatusUpdateView):
    form_class = LiveToDisabledReviewRejectRolloutForm


class DisabledToLiveReviewRolloutView(StatusUpdateView):
    form_class = DisabledToLiveReviewRolloutForm


class DisabledToLiveDuplicatePhaseReviewRolloutView(StatusUpdateView):
    form_class = DisabledToLiveDuplicatePhaseReviewRolloutForm


class DisabledToLiveReviewApproveRolloutView(StatusUpdateView):
    form_class = DisabledToLiveReviewApproveRolloutForm


class DisabledToLiveReviewRejectRolloutView(StatusUpdateView):
    form_class = DisabledToLiveReviewRejectRolloutForm


class NewRolloutScheduleUpdateView(NewCardUpdateView):
    form_class = RolloutScheduleForm
    display_template = "new/rollouts/schedule/card.html"
    template_name = "new/rollouts/schedule/edit_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_plan = self.request.POST.get("template_name") or self.request.POST.get(
            "rollout_plan"
        )
        if selected_plan:
            context["form"].initial["rollout_plan"] = selected_plan
        return context

    def can_edit(self):
        return self.object.is_draft or self.object.is_rolling_out


class NewRolloutPhaseCreateView(
    RenderParentDBResponseMixin, NewRolloutScheduleUpdateView
):
    form_class = RolloutPhaseCreateForm


class NewRolloutPhaseDeleteView(CardMutationMixin, NewRolloutScheduleUpdateView):
    form_class = RolloutPhaseDeleteForm

    def mutate(self, form):
        phase_id = self.request.POST.get("phase_id")
        if not phase_id:
            return
        if int(phase_id) not in form.locked_phase_ids:
            self.object.rollout_phases.filter(id=phase_id).delete()


class NewRolloutPlanCreateView(RenderParentDBResponseMixin, NewRolloutScheduleUpdateView):
    form_class = RolloutPlanCreateForm


class NewRolloutPlanApplyView(CardMutationMixin, NewRolloutScheduleUpdateView):
    form_class = RolloutPlanApplyForm

    def mutate(self, form):
        form.apply_plan()


class NewSubscribeView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    model = NimbusExperiment
    form_class = SubscribeForm
    template_name = "new/common/subscribe_bell.html"

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data())


class NewUnsubscribeView(NewSubscribeView):
    form_class = UnsubscribeForm


class NewCloneView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    form_class = NimbusExperimentSidebarCloneForm
    template_name = "new/common/clone_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["data"] = kwargs["data"].copy()
        kwargs["data"]["owner"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        return super().get_context_data(experiment=self.get_object(), **kwargs)

    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)
        if response.status_code == 302:
            response = HttpResponse()
            response.headers["HX-Redirect"] = reverse(
                "new-nimbus-ui-rollout-detail", kwargs={"slug": self.object.slug}
            )
        return response


class NewToggleArchiveView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    form_class = ToggleArchiveForm
    template_name = "new/common/base.html"

    def form_valid(self, form):
        form.save()
        response = HttpResponse()
        if self.request.headers.get("HX-Request"):
            response.headers["HX-Refresh"] = "true"
        return response


class NewToggleReviewSlackNotificationsView(
    NimbusExperimentViewMixin, RequestFormMixin, UpdateView
):
    model = NimbusExperiment
    form_class = ToggleReviewSlackNotificationsForm
    template_name = "new/common/slack_notifications_toggle.html"

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data())
