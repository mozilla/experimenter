from django.conf import settings
from django.views.generic import DetailView, TemplateView
from django_filters.views import FilterView

from experimenter.legacy.legacy_experiments.filtersets import ExperimentFilterset
from experimenter.legacy.legacy_experiments.forms import ExperimentOrderingForm
from experimenter.legacy.legacy_experiments.models import Experiment


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


class ExperimentDetailView(DetailView):
    model = Experiment
    queryset = Experiment.objects.get_prefetched()

    def get_template_names(self):
        return [
            "experiments/detail_{status}.html".format(
                status=self.object.status.lower()  # OSX is case insensitive
            ),
            "experiments/detail_base.html",
        ]


class NimbusUIView(TemplateView):
    template_name = "nimbus/index.html"


class PageNotFoundView(TemplateView):
    template_name = "404.html"

    @classmethod
    def as_404_view(cls):
        as_view_fn = cls.as_view()

        def view_fn(request, exception):
            response = as_view_fn(request)
            response.status_code = 404
            response.render()
            return response

        return view_fn
