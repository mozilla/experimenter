from django.urls import reverse
from django.views.generic import DetailView

from experimenter.nimbus_ui.filtersets import (
    TagSearchFilterSet,
    UserSearchFilterSet,
)
from experimenter.nimbus_ui.forms import (
    AudienceForm,
    CollaboratorsForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    OverviewForm,
    QAStatusForm,
    TagAssignForm,
)
from experimenter.nimbus_ui.views import (
    CloneExperimentFormMixin,
    NimbusExperimentViewMixin,
    OverviewUpdateView,
    RenderParentDBResponseMixin,
)


class NimbusRolloutDetailView(
    NimbusExperimentViewMixin,
    CloneExperimentFormMixin,
    DetailView,
):
    template_name = "nimbus_experiments/new_designs/rollouts/rollout_detail.html"


class OverviewCardMixin:
    template_name = "nimbus_experiments/new_designs/rollouts/overview/edit_form.html"
    cancel_url_name = "new-nimbus-ui-rollout-detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not isinstance(kwargs.get("form"), OverviewForm):
            context["form"] = OverviewForm(instance=self.object)
        context["cancel_url"] = reverse(
            self.cancel_url_name, kwargs={"slug": self.object.slug}
        )
        return context


class RisksCardMixin:
    template_name = "nimbus_experiments/new_designs/rollouts/risks/edit_form.html"
    cancel_url_name = "new-nimbus-ui-rollout-detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not isinstance(kwargs.get("form"), OverviewForm):
            context["form"] = OverviewForm(instance=self.object)
        context["cancel_url"] = reverse(
            self.cancel_url_name, kwargs={"slug": self.object.slug}
        )
        return context


class QACardMixin:
    template_name = "nimbus_experiments/new_designs/rollouts/qa/edit_form.html"
    cancel_url_name = "new-nimbus-ui-rollout-detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not isinstance(kwargs.get("form"), QAStatusForm):
            context["form"] = QAStatusForm(instance=self.object)
        context["cancel_url"] = reverse(
            self.cancel_url_name, kwargs={"slug": self.object.slug}
        )
        return context


class AudienceCardMixin:
    template_name = "nimbus_experiments/new_designs/rollouts/audience/edit_form.html"
    cancel_url_name = "new-nimbus-ui-rollout-detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not isinstance(kwargs.get("form"), AudienceForm):
            context["form"] = AudienceForm(
                instance=self.object,
                rollout_card_view=True,
            )
        context["cancel_url"] = reverse(
            self.cancel_url_name, kwargs={"slug": self.object.slug}
        )
        return context


class NewCardUpdateView(OverviewUpdateView):
    display_template = None

    def form_valid(self, form):
        self.object = form.save()
        context = self.get_context_data()
        context["hx_swap_oob"] = True
        return self.response_class(
            request=self.request,
            template=self.display_template,
            context=context,
        )


class NewOverviewUpdateView(OverviewCardMixin, NewCardUpdateView):
    display_template = "nimbus_experiments/new_designs/rollouts/overview/card.html"


class NewRisksUpdateView(RisksCardMixin, NewCardUpdateView):
    display_template = "nimbus_experiments/new_designs/rollouts/risks/card.html"


class NewAudienceUpdateView(AudienceCardMixin, NewCardUpdateView):
    form_class = AudienceForm
    display_template = "nimbus_experiments/new_designs/rollouts/audience/card.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["rollout_card_view"] = True
        return kwargs


class NewQAUpdateView(QACardMixin, NewCardUpdateView):
    form_class = QAStatusForm
    display_template = "nimbus_experiments/new_designs/rollouts/qa/card.html"


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
    template_name = (
        "nimbus_experiments/new_designs/rollouts/overview/tag_search_results.html"
    )
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


class NewTagView(NewM2MDeltaMixin, OverviewCardMixin, NewCardUpdateView):
    item_id_key = "tag_id"
    m2m_attr = "tags"
    form_field = "tags"
    form_class = TagAssignForm
    display_template = "nimbus_experiments/new_designs/rollouts/overview/card.html"


class NewAddTagView(NewTagView):
    add = True


class NewRemoveTagView(NewTagView):
    add = False


class NewSubscriberSearchView(NewM2MSearchView):
    template_name = (
        "nimbus_experiments/new_designs/rollouts/overview/subscriber_search_results.html"
    )
    m2m_attr = "subscribers"
    context_key = "users"
    filterset_class = UserSearchFilterSet
    ordering = "email"
    require_query = True


class NewSubscriberView(NewM2MDeltaMixin, OverviewCardMixin, NewCardUpdateView):
    item_id_key = "user_id"
    m2m_attr = "subscribers"
    form_field = "collaborators"
    form_class = CollaboratorsForm
    display_template = "nimbus_experiments/new_designs/rollouts/overview/card.html"


class NewAddSubscriberView(NewSubscriberView):
    add = True


class NewRemoveSubscriberView(NewSubscriberView):
    add = False
