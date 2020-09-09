from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from experimenter.experiments.models import ExperimentRapid
from experimenter.experiments.api.v3.serializers import (
    ExperimentRapidSerializer,
    ExperimentRapidStatusSerializer,
)


class ExperimentRapidViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ExperimentRapidSerializer
    queryset = ExperimentRapid.objects.all()
    lookup_field = "slug"

    @action(detail=True, methods=["post"])
    def request_review(self, request, slug=None):
        instance = self.get_object()
        update_data = {"status": ExperimentRapid.STATUS_REVIEW}
        serializer = ExperimentRapidStatusSerializer(
            instance, data=update_data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
