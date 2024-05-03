from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v6.views import (
    NimbusExperimentDraftViewSet,
    NimbusExperimentFirstRunViewSet,
    NimbusExperimentViewSet,
)

router = SimpleRouter()
router.register(r"experiments", NimbusExperimentViewSet, "nimbus-experiment-rest-v6")
router.register(
    r"experiments-first-run",
    NimbusExperimentFirstRunViewSet,
    "nimbus-experiment-rest-v6-first-run",
)
router.register(
    r"draft-experiments",
    NimbusExperimentDraftViewSet,
    "nimbus-experiment-rest-v6-draft",
)
urlpatterns = router.urls
