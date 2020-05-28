from django.conf.urls import url

from experimenter.experiments.api.v1.views import (
    ExperimentCSVListView,
    ExperimentDetailView,
    ExperimentListView,
    ExperimentRecipeView,
)


urlpatterns = [
    url(r"^csv/$", ExperimentCSVListView.as_view(), name="experiments-api-csv",),
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
