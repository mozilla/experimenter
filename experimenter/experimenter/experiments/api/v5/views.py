from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.api.v5.serializers import (
    FmlFeatureValueSerializer,
    NimbusExperimentCsvSerializer,
)
from experimenter.experiments.models import NimbusExperiment


class NimbusExperimentCsvRenderer(CSVRenderer):
    header = NimbusExperimentCsvSerializer.Meta.fields
    labels = {field: field.replace("_", " ").title() for field in header}


class NimbusExperimentCsvListView(ListAPIView):
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


class FmlErrorsView(UpdateAPIView):
    queryset = NimbusExperiment.objects.all()
    lookup_field = "slug"
    serializer_class = FmlFeatureValueSerializer
