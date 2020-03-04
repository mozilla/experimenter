from django.conf.urls import url

from experimenter.experiments.api_views import (
    ExperimentCloneView,
    ExperimentDesignAddonView,
    ExperimentDesignBranchedAddonView,
    ExperimentDesignGenericView,
    ExperimentDesignMultiPrefView,
    ExperimentDesignPrefView,
    ExperimentDesignRolloutView,
    ExperimentDetailView,
    ExperimentListView,
    ExperimentRecipeView,
    ExperimentSendIntentToShipEmailView,
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
