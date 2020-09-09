from rest_framework import viewsets, mixins

from experimenter.experiments.models import ExperimentRapid
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer


class ExperimentRapidViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "recipe_slug"
    queryset = ExperimentRapid.objects.exclude(
        status__in=[ExperimentRapid.STATUS_DRAFT, ExperimentRapid.STATUS_REVIEW]
    )
    serializer_class = ExperimentRapidRecipeSerializer
