from django.conf.urls import url

from experimenter.experiments.api_views import (
    ExperimentCloneView,
    ExperimentDesignAddonView,
    ExperimentDesignBranchedAddonView,
    ExperimentDesignGenericView,
    ExperimentDesignMultiPrefView,
    ExperimentDesignPrefView,
    ExperimentDesignRolloutView,
    ExperimentSendIntentToShipEmailView,
)


urlpatterns = [
    url(
        r"^(?P<slug>[\w-]+)/intent-to-ship-email$",
        ExperimentSendIntentToShipEmailView.as_view(),
        name="experiments-api-send-intent-to-ship-email",
    ),
    url(
        r"^(?P<slug>[\w-]+)/clone",
        ExperimentCloneView.as_view(),
        name="experiments-api-clone",
    ),
    url(
        r"^(?P<slug>[\w-]+)/design-addon",
        ExperimentDesignAddonView.as_view(),
        name="experiments-design-addon",
    ),
    url(
        r"^(?P<slug>[\w-]+)/design-pref",
        ExperimentDesignPrefView.as_view(),
        name="experiments-design-pref",
    ),
    url(
        r"^(?P<slug>[\w-]+)/design-multi-pref",
        ExperimentDesignMultiPrefView.as_view(),
        name="experiments-design-multi-pref",
    ),
    url(
        r"^(?P<slug>[\w-]+)/design-generic",
        ExperimentDesignGenericView.as_view(),
        name="experiments-design-generic",
    ),
    url(
        r"^(?P<slug>[\w-]+)/design-branched-addon",
        ExperimentDesignBranchedAddonView.as_view(),
        name="experiments-design-branched-addon",
    ),
    url(
        r"^(?P<slug>[\w-]+)/design-rollout",
        ExperimentDesignRolloutView.as_view(),
        name="experiments-design-rollout",
    ),
]
