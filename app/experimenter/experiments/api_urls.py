from django.conf.urls import url

from experimenter.experiments.api_views import (
    ExperimentAcceptView,
    ExperimentDetailView,
    ExperimentListView,
    ExperimentRecipeView,
    ExperimentRejectView,
    ExperimentSendIntentToShipEmailView,
)


urlpatterns = [
    url(
        r"^(?P<slug>[\w-]+)/accept/$",
        ExperimentAcceptView.as_view(),
        name="experiments-api-accept",
    ),
    url(
        r"^(?P<slug>[\w-]+)/reject/$",
        ExperimentRejectView.as_view(),
        name="experiments-api-reject",
    ),
    url(
        r"^(?P<slug>[\w-]+)/intent-to-ship-email$",
        ExperimentSendIntentToShipEmailView.as_view(),
        name="experiments-api-send-intent-to-ship-email",
    ),
    url(
        r"^(?P<slug>[\w-]+)/recipe/$",
        ExperimentRecipeView.as_view(),
        name="experiments-api-recipe",
    ),
    url(
        r"^(?P<slug>[\w-]+)/$",
        ExperimentDetailView.as_view(),
        name="experiments-api-detail",
    ),
    url(r"^$", ExperimentListView.as_view(), name="experiments-api-list"),
]
