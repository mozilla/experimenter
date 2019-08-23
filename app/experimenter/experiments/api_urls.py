from django.conf.urls import url

from experimenter.experiments.api_views import (
    ExperimentDetailView,
    ExperimentListView,
    ExperimentRecipeView,
    ExperimentSendIntentToShipEmailView,
    ExperimentCloneView,
)


urlpatterns = [
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
    url(
        r"^(?P<slug>[\w-]+)/clone",
        ExperimentCloneView.as_view(),
        name="experiments-api-clone",
    ),
]
