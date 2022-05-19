from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView

from experimenter.experiments.api.v5.views import NimbusExperimentCSVListView

urlpatterns = [
    url(
        r"graphql",
        csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True)),
        name="nimbus-api-graphql",
    ),
    url(
        r"^csv/$",
        NimbusExperimentCSVListView.as_view(),
        name="nimbus-experiments-api-csv",
    ),
]
