from django.conf.urls import url

from experimenter.legacy.legacy_experiments.api.v1.views import (
    ExperimentDetailView,
    ExperimentListView,
    ExperimentRecipeView,
)

urlpatterns = [
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
