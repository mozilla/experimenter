from django.urls import re_path

from experimenter.legacy.legacy_experiments.api.v1.views import (
    ExperimentDetailView,
    ExperimentListView,
    ExperimentRecipeView,
)

urlpatterns = [
    re_path(
        r"^(?P<slug>[\w-]+)/recipe/$",
        ExperimentRecipeView.as_view(),
        name="experiments-api-recipe",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/$",
        ExperimentDetailView.as_view(),
        name="experiments-api-detail",
    ),
    re_path(r"^$", ExperimentListView.as_view(), name="experiments-api-list"),
]
