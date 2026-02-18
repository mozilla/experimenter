from django_filters import FilterSet, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from experimenter.experiments.api.cache import CachedListMixin
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureConfig


class BaseExperimentFilterSet(FilterSet):
    application = filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Application.choices,
    )

    feature_config = filters.ModelMultipleChoiceFilter(
        queryset=NimbusFeatureConfig.objects.all(),
        field_name="feature_configs__slug",
        to_field_name="slug",
    )

    class Meta:
        model = NimbusExperiment
        fields = ("is_localized",)


class NimbusExperimentFilterSet(BaseExperimentFilterSet):
    class Meta:
        model = NimbusExperiment
        fields = (*BaseExperimentFilterSet.Meta.fields, "is_first_run", "status")


class NimbusDraftExperimentFilterSet(BaseExperimentFilterSet):
    class Meta:
        model = NimbusExperiment
        fields = (*BaseExperimentFilterSet.Meta.fields, "is_first_run")


class NimbusExperimentViewSet(
    CachedListMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "slug"
    queryset = (
        NimbusExperiment.objects.with_related()
        .exclude(status__in=[NimbusExperiment.Status.DRAFT])
        .order_by("slug")
    )
    serializer_class = NimbusExperimentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = NimbusExperimentFilterSet
    cache_key_prefix = "v6:experiments"


class NimbusExperimentDraftViewSet(NimbusExperimentViewSet):
    filterset_class = NimbusDraftExperimentFilterSet
    cache_key_prefix = "v6:draft-experiments"

    queryset = (
        NimbusExperiment.objects.with_related()
        .filter(status=NimbusExperiment.Status.DRAFT)
        .order_by("slug")
    )


class NimbusExperimentFirstRunViewSet(NimbusExperimentViewSet):
    filterset_class = BaseExperimentFilterSet
    cache_key_prefix = "v6:first-run"

    queryset = (
        NimbusExperiment.objects.with_related()
        .filter(status=NimbusExperiment.Status.LIVE)
        .filter(is_first_run=True)
        .order_by("slug")
    )
