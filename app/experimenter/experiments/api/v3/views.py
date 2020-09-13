from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from experimenter.experiments.api.v3.serializers import (
    ExperimentRapidSerializer,
    ExperimentRapidStatusSerializer,
)
from experimenter.experiments.models import Experiment


class ExperimentRapidViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ExperimentRapidSerializer
    queryset = Experiment.objects.filter(type=Experiment.TYPE_RAPID)
    lookup_field = "slug"

    @action(detail=True, methods=["post"])
    def request_review(self, request, slug=None):
        instance = self.get_object()
        update_data = {"status": Experiment.STATUS_REVIEW}
        serializer = ExperimentRapidStatusSerializer(
            instance, data=update_data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
