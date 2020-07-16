from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)

from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v4.serializers import (
    ExperimentRapidSerializer,
    ExperimentRapidRecipeSerializer,
)


class ExperimentListView(ListAPIView):
    filter_fields = ("status",)
    queryset = Experiment.objects.get_prefetched().filter(type=Experiment.TYPE_RAPID)
    serializer_class = ExperimentRapidSerializer


class ExperimentRapidDetailsView(RetrieveAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.get_prefetched()
    serializer_class = ExperimentRapidSerializer


class ExperimentRapidRecipeView(RetrieveAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.get_prefetched().filter(
        status__in=(
            Experiment.STATUS_SHIP,
            Experiment.STATUS_ACCEPTED,
            Experiment.STATUS_LIVE,
            Experiment.STATUS_COMPLETE,
        )
    )
    serializer_class = ExperimentRapidRecipeSerializer
