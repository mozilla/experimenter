import csv

from django.http import HttpResponse
from rest_framework.generics import ListAPIView, RetrieveAPIView

from experimenter.experiments.api.v5.serializers import (
    NimbusConfigurationDataClass,
    NimbusConfigurationSerializer,
    NimbusExperimentCsvSerializer,
)
from experimenter.experiments.models import NimbusExperiment


class NimbusExperimentCsvListView(ListAPIView):
    queryset = (
        NimbusExperiment.objects.select_related("owner")
        .prefetch_related("feature_configs", "changes")
        .filter(is_archived=False)
    )

    def get_queryset(self):
        return sorted(
            super().get_queryset(),
            key=lambda experiment: (
                experiment.start_date and experiment.start_date.strftime("%Y-%m-%d")
            )
            or "",
            reverse=True,
        )

    serializer_class = NimbusExperimentCsvSerializer

    def get_serializer(self, queryset, many=True):
        return self.serializer_class(
            queryset,
            many=many,
        )

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="experimenter-report.csv"'

        serializer = self.get_serializer(self.get_queryset(), many=True)
        header = NimbusExperimentCsvSerializer.Meta.fields
        writer = csv.DictWriter(response, fieldnames=header)
        writer.writeheader()
        for row in serializer.data:
            writer.writerow(row)

        return response


class NimbusConfigurationView(RetrieveAPIView):
    serializer_class = NimbusConfigurationSerializer

    def get_object(self):
        return NimbusConfigurationDataClass()
