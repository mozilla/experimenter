from rest_framework.generics import ListAPIView, RetrieveAPIView

from experimenter.legacy.legacy_experiments.api.v1.serializers import (
    ExperimentSerializer,
)
from experimenter.legacy.legacy_experiments.constants import ExperimentConstants
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.legacy.normandy.serializers import ExperimentRecipeSerializer


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
