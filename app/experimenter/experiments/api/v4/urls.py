from django.conf.urls import url
from experimenter.experiments.api.v4.views import (
    ExperimentListView,
    ExperimentRapidDetailsView,
    ExperimentRapidRecipeView,
)


urlpatterns = [
    url(
        r"^experiments$", ExperimentListView.as_view(), name="experiments-rapid-api-list",
    ),
    url(
        r"^experiments/(?P<slug>[\w-]+)$",
        ExperimentRapidDetailsView.as_view(),
        name="experiments-rapid-details-read",
    ),
    url(
        r"^experiments/(?P<slug>[\w-]+)/recipe/$",
        ExperimentRapidRecipeView.as_view(),
        name="experiments-rapid-recipe",
    ),
]
