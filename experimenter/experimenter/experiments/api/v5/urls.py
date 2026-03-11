from django.urls import path, re_path

from experimenter.experiments.api.v5.views import (
    FmlErrorsView,
    NimbusExperimentCsvListView,
    NimbusExperimentYamlListView,
)

urlpatterns = [
    re_path(
        r"^csv/$",
        NimbusExperimentCsvListView.as_view(),
        name="nimbus-experiments-csv",
    ),
    re_path(
        r"^yaml/$",
        NimbusExperimentYamlListView.as_view(),
        name="nimbus-experiments-yaml",
    ),
    path(r"fml-errors/<slug:slug>/", FmlErrorsView.as_view(), name="nimbus-fml-errors"),
]
