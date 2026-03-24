from django_filters import FilterSet, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from experimenter.experiments.api.cache import CachedListMixin
from experimenter.experiments.api.v7.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureConfig


class NimbusExperimentFilterSet(FilterSet):
    status = filters.MultipleChoiceFilter(
        choices=NimbusExperiment.Status.choices,
    )
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
        fields = (
            "status",
            "application",
            "feature_config",
        )


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
    cache_key_prefix = "v7:experiments"
