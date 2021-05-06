import json

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django.views.generic.edit import ModelFormMixin
from django_filters.views import FilterView

from experimenter.base.models import Country, Locale
from experimenter.experiments.email import send_experiment_comment_email
from experimenter.experiments.filtersets import ExperimentFilterset
from experimenter.experiments.forms import (
    ExperimentArchiveForm,
    ExperimentCommentForm,
    ExperimentObjectivesForm,
    ExperimentOrderingForm,
    ExperimentOverviewForm,
    ExperimentResultsForm,
    ExperimentReviewForm,
    ExperimentRisksForm,
    ExperimentStatusForm,
    ExperimentSubscribedForm,
    NormandyIdForm,
)
from experimenter.experiments.models import Experiment


class ExperimentListView(FilterView):
    context_object_name = "experiments"
    filterset_class = ExperimentFilterset
    model = Experiment
    template_name = "experiments/list.html"
    paginate_by = settings.EXPERIMENTS_PAGINATE_BY
    queryset = Experiment.objects.get_prefetched()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ordering_form = None

    def get_filterset_kwargs(self, *args, **kwargs):
        kwargs = super().get_filterset_kwargs(*args, **kwargs)

        # Always pass in request.GET otherwise the
        # filterset form will be unbound and our custom
        # validation won't kick in
        kwargs["data"] = self.request.GET
        return kwargs

    def get_ordering(self):
        self.ordering_form = ExperimentOrderingForm(self.request.GET)

        if self.ordering_form.is_valid():
            return self.ordering_form.cleaned_data["ordering"]

        return self.ordering_form.ORDERING_CHOICES[0][0]

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(ordering_form=self.ordering_form, *args, **kwargs)


class ExperimentFormMixin(object):
    model = Experiment

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        if "action" in self.request.POST and self.request.POST["action"] == "continue":
            return reverse(self.next_view_name, kwargs={"slug": self.object.slug})

        return reverse("experiments-detail", kwargs={"slug": self.object.slug})


class ExperimentCreateView(ExperimentFormMixin, CreateView):
    form_class = ExperimentOverviewForm
    next_view_name = "experiments-timeline-pop-update"
    template_name = "experiments/edit_overview.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["owner"] = self.request.user.id
        return initial


class ExperimentOverviewUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentOverviewForm
    next_view_name = "experiments-timeline-pop-update"
    template_name = "experiments/edit_overview.html"


class ExperimentTimelinePopulationUpdateView(DetailView):
    model = Experiment
    template_name = "experiments/edit_timeline_population.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["locales"] = json.dumps(
            list(
                Locale.objects.extra(select={"label": "name", "value": "id"}).values(
                    "label", "value"
                )
            )
        )
        context["countries"] = json.dumps(
            list(
                Country.objects.extra(select={"label": "name", "value": "id"}).values(
                    "label", "value"
                )
            )
        )

        return context


class ExperimentDesignUpdateView(DetailView):
    model = Experiment
    template_name = "experiments/edit_design.html"


class ExperimentObjectivesUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentObjectivesForm
    next_view_name = "experiments-risks-update"
    template_name = "experiments/edit_objectives.html"


class ExperimentRisksUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentRisksForm
    next_view_name = "experiments-detail"
    template_name = "experiments/edit_risks.html"


class ExperimentResultsUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentResultsForm
    next_view_name = "experiments-detail"
    template_name = "experiments/edit_results.html"


class ExperimentDetailView(ExperimentFormMixin, ModelFormMixin, DetailView):
    model = Experiment
    form_class = ExperimentReviewForm
    queryset = Experiment.objects.get_prefetched()

    def get_template_names(self):
        return [
            "experiments/detail_{status}.html".format(
                status=self.object.status.lower()  # OSX is case insensitive
            ),
            "experiments/detail_base.html",
        ]

    def get_context_data(self, *args, **kwargs):
        if "normandy_id" in self.request.GET:
            normandy_id_form = NormandyIdForm(
                request=self.request, data=self.request.GET, instance=self.object
            )
        else:
            normandy_id_form = NormandyIdForm(request=self.request, instance=self.object)

        return super().get_context_data(
            normandy_id_form=normandy_id_form, *args, **kwargs
        )


class ExperimentStatusUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentStatusForm
    model = Experiment

    def form_invalid(self, form):
        return redirect(reverse("experiments-detail", kwargs={"slug": self.object.slug}))


class ExperimentReviewUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentReviewForm
    model = Experiment


class ExperimentArchiveUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentArchiveForm
    model = Experiment


class ExperimentSubscribedUpdateView(ExperimentFormMixin, UpdateView):
    form_class = ExperimentSubscribedForm
    model = Experiment


class ExperimentNormandyUpdateView(ExperimentFormMixin, UpdateView):
    form_class = NormandyIdForm
    model = Experiment

    def form_valid(self, form):
        response = super().form_valid(form)
        status_form = ExperimentStatusForm(
            request=self.request,
            data={"status": Experiment.STATUS_ACCEPTED},
            instance=self.object,
        )
        status_form.save()
        return response

    def form_invalid(self, form):
        url = reverse("experiments-detail", kwargs={"slug": self.kwargs["slug"]})
        query_parameters = form.data.copy()
        query_parameters.pop("csrfmiddlewaretoken", None)

        return redirect(f"{url}?{query_parameters.urlencode()}")


class ExperimentCommentCreateView(ExperimentFormMixin, CreateView):
    form_class = ExperimentCommentForm

    def form_valid(self, form):
        comment = form.save()
        send_experiment_comment_email(comment)
        return redirect(
            "{url}#{section}-comments".format(
                url=reverse("experiments-detail", kwargs={"slug": self.kwargs["slug"]}),
                section=comment.section,
            )
        )

    def form_invalid(self, form):
        return redirect(
            reverse("experiments-detail", kwargs={"slug": self.kwargs["slug"]})
        )


class NimbusUIView(TemplateView):
    template_name = "nimbus/index.html"


class PageNotFoundView(TemplateView):
    template_name = "nimbus/404.html"

    @classmethod
    def as_404_view(cls):
        as_view_fn = cls.as_view()

        def view_fn(request, exception):
            response = as_view_fn(request)
            response.status_code = 404
            response.render()
            return response

        return view_fn
