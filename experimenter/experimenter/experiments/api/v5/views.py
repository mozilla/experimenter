import yaml
from django.db.models import F
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import BaseRenderer
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.api.cache import CachedListMixin
from experimenter.experiments.api.v5.serializers import (
    FmlFeatureValueSerializer,
    NimbusExperimentCsvSerializer,
    NimbusExperimentYamlSerializer,
)
from experimenter.experiments.models import NimbusExperiment


class NimbusExperimentCsvRenderer(CSVRenderer):
    header = NimbusExperimentCsvSerializer.Meta.fields
    labels = {field: field.replace("_", " ").title() for field in header}


class NimbusExperimentCsvListView(CachedListMixin, ListAPIView):
    cache_key_prefix = "v5:csv"
    cache_content_type = "text/csv; charset=utf-8"
    queryset = (
        NimbusExperiment.objects.select_related("owner")
        .prefetch_related("feature_configs")
        .filter(is_archived=False)
    )
    serializer_class = NimbusExperimentCsvSerializer
    renderer_classes = (NimbusExperimentCsvRenderer,)

    def get_queryset(self):
        return sorted(
            super().get_queryset(),
            key=lambda experiment: (
                (experiment.start_date and experiment.start_date.strftime("%Y-%m-%d"))
                or ""
            ),
            reverse=True,
        )


class NimbusExperimentYamlRenderer(BaseRenderer):
    media_type = "text/yaml"
    format = "yaml"
    charset = "utf-8"

    @staticmethod
    def _strip_empty(obj):
        if isinstance(obj, dict):
            return {
                k: NimbusExperimentYamlRenderer._strip_empty(v)
                for k, v in obj.items()
                if v is not None and v != "" and v != [] and v != {}
            }
        if isinstance(obj, list):
            return [NimbusExperimentYamlRenderer._strip_empty(i) for i in obj]
        return obj

    def render(self, data, accepted_media_type=None, renderer_context=None):
        experiments = [self._strip_empty(exp) for exp in data["results"]]
        output = {
            **{k: v for k, v in data.items() if k != "results"},
            "experiments": experiments,
        }
        return yaml.dump(
            output,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


class YamlExportPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = None
    max_page_size = 100


class NimbusExperimentYamlListView(CachedListMixin, ListAPIView):
    cache_key_prefix = "v5:yaml"
    cache_content_type = "text/yaml; charset=utf-8"
    queryset = (
        NimbusExperiment.objects.select_related("owner", "reference_branch", "parent")
        .prefetch_related(
            "feature_configs",
            "branches",
            "branches__feature_values__feature_config",
            "documentation_links",
            "projects",
            "locales",
            "countries",
            "languages",
            "tags",
            "required_experiments",
            "excluded_experiments",
        )
        .filter(is_archived=False, status=NimbusExperiment.Status.COMPLETE)
        .order_by(F("_start_date").desc(nulls_last=True), "-id")
    )
    serializer_class = NimbusExperimentYamlSerializer
    renderer_classes = (NimbusExperimentYamlRenderer,)
    pagination_class = YamlExportPagination


class FmlErrorsView(UpdateAPIView):
    queryset = NimbusExperiment.objects.all()
    lookup_field = "slug"
    serializer_class = FmlFeatureValueSerializer
