from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from experimenter.experiments.api.v5.serializers import NimbusRolloutReviewSerializer
from experimenter.experiments.models import NimbusExperiment, Tag
from experimenter.nimbus_ui.filtersets import (
    TagSearchFilterSet,
    UserSearchFilterSet,
)
from experimenter.nimbus_ui.new.forms import (
    CollaboratorsForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    NimbusExperimentCreateForm,
    NimbusExperimentSidebarCloneForm,
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
        return context


class NimbusRolloutDetailView(
    RolloutSetupProgressMixin,
    NimbusExperimentViewMixin,
    CloneExperimentFormMixin,
    DetailView,
):
    template_name = "new/rollouts/rollout_detail.html"


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


class NewRisksUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutRisksForm
    display_template = "new/rollouts/risks/card.html"
    template_name = "new/rollouts/risks/edit_form.html"


class NewAudienceUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutAudienceForm
    display_template = "new/rollouts/audience/card.html"
    template_name = "new/rollouts/audience/edit_form.html"


class NewRolloutFeaturesUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutFeaturesForm
    display_template = "new/rollouts/rollout_features/card.html"
    template_name = "new/rollouts/rollout_features/edit_form.html"

    def render_valid_response(self):
        self.object.refresh_from_db()

        # If the request came from the explicit Save button, return the read-only card
        # view so the UI swaps back to the card. When the form is posted for intermediate
        # updates (e.g. feature_configs changed via hx-post on change), return the
        # editable form so the user can continue editing.
        if "save" in self.request.POST:
            return super().render_valid_response()

        return self.render_to_response(self.get_context_data())


class NewRolloutScreenshotCreateView(
    RenderParentDBResponseMixin, NewRolloutFeaturesUpdateView
):
    form_class = RolloutScreenshotCreateForm


class NewRolloutScreenshotDeleteView(
    RenderParentDBResponseMixin, NewRolloutFeaturesUpdateView
):
    form_class = RolloutScreenshotDeleteForm


class NewQAUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutQAStatusForm
    display_template = "new/rollouts/qa/card.html"
    template_name = "new/rollouts/qa/edit_form.html"


class NewSignoffUpdateView(CardMixin, NewCardUpdateView):
    form_class = RolloutSignoffForm
    display_template = "new/rollouts/signoff/card.html"
    template_name = "new/rollouts/signoff/edit_form.html"


class NewDocumentationLinkCreateView(RenderParentDBResponseMixin, NewOverviewUpdateView):
    form_class = DocumentationLinkCreateForm


class NewDocumentationLinkDeleteView(RenderParentDBResponseMixin, NewOverviewUpdateView):
    form_class = DocumentationLinkDeleteForm


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


class NewTagView(NewM2MDeltaMixin, CardMixin, NewCardUpdateView):
    item_id_key = "tag_id"
    m2m_attr = "tags"
    form_field = "tags"
    form_class = TagAssignForm
    display_template = "new/rollouts/overview/card.html"
    template_name = "new/rollouts/overview/edit_form.html"


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


class NewSubscriberView(NewM2MDeltaMixin, CardMixin, NewCardUpdateView):
    item_id_key = "user_id"
    m2m_attr = "subscribers"
    form_field = "collaborators"
    form_class = CollaboratorsForm
    display_template = "new/rollouts/overview/card.html"
    template_name = "new/rollouts/overview/edit_form.html"


class NewAddSubscriberView(NewSubscriberView):
    add = True


class NewRemoveSubscriberView(NewSubscriberView):
    add = False


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
        return self.object.can_edit_schedule()


class NewRolloutPhaseCreateView(
    RenderParentDBResponseMixin, NewRolloutScheduleUpdateView
):
    form_class = RolloutPhaseCreateForm


class NewRolloutPhaseDeleteView(
    RenderParentDBResponseMixin, NewRolloutScheduleUpdateView
):
    form_class = RolloutPhaseDeleteForm


class NewRolloutPlanCreateView(RenderParentDBResponseMixin, NewRolloutScheduleUpdateView):
    form_class = RolloutPlanCreateForm


class NewRolloutPlanApplyView(RenderParentDBResponseMixin, NewRolloutScheduleUpdateView):
    form_class = RolloutPlanApplyForm


class NewSubscribeView(NimbusExperimentViewMixin, RequestFormMixin, UpdateView):
    model = NimbusExperiment
    form_class = SubscribeForm
    template_name = "new/common/subscribe_bell.html"

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data())


class NewUnsubscribeView(NewSubscribeView):
    form_class = UnsubscribeForm


class NewToggleReviewSlackNotificationsView(
    NimbusExperimentViewMixin, RequestFormMixin, UpdateView
):
    model = NimbusExperiment
    form_class = ToggleReviewSlackNotificationsForm
    template_name = "new/common/slack_notifications_toggle.html"

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data())
