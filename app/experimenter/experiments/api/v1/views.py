from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v1.serializers import (
    ExperimentSerializer,
    ExperimentCSVSerializer,
)
from experimenter.experiments.filtersets import ExperimentFilterset
from experimenter.normandy.serializers import ExperimentRecipeSerializer


class ExperimentListView(ListAPIView):
    filter_fields = ("status",)
    queryset = Experiment.objects.get_prefetched()
    serializer_class = ExperimentSerializer


class ExperimentDetailView(RetrieveAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.get_prefetched()
    serializer_class = ExperimentSerializer


class ExperimentRecipeView(RetrieveAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.get_prefetched().filter(
        status__in=(
            ExperimentConstants.STATUS_SHIP,
            ExperimentConstants.STATUS_ACCEPTED,
            ExperimentConstants.STATUS_LIVE,
            ExperimentConstants.STATUS_COMPLETE,
        )
    )
    serializer_class = ExperimentRecipeSerializer


class ExperimentCSVListView(ListAPIView):
    queryset = Experiment.objects.get_prefetched().order_by("status", "name")
    serializer_class = ExperimentCSVSerializer
    renderer_classes = (CSVRenderer,)

    def get_queryset(self):
        return ExperimentFilterset(
            self.request.GET, super().get_queryset(), request=self.request
        ).qs

    def get_renderer_context(self):
        # Pass the ordered list of fields in to specify the ordering of the headers
        # otherwise it defaults to sorting them alphabetically
        context = super().get_renderer_context()
        context["header"] = self.serializer_class.Meta.fields
        return context
