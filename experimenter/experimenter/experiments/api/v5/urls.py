from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView

from experimenter.experiments.api.v5.views import (
    FmlErrorsView,
    NimbusExperimentCsvListView,
    NimbusExperimentYamlListView,
)

urlpatterns = [
    re_path(
        r"graphql",
        csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True)),
        name="nimbus-api-graphql",
    ),
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
