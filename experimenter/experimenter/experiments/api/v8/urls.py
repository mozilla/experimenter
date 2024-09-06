from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v8.views import (
    NimbusExperimentDraftViewSet,
    NimbusExperimentFirstRunViewSet,
    NimbusExperimentViewSet,
)

router = SimpleRouter()
router.register(r"experiments", NimbusExperimentViewSet, "nimbus-experiment-rest-v8")
router.register(
    r"experiments-first-run",
    NimbusExperimentFirstRunViewSet,
    "nimbus-experiment-rest-v8-first-run",
)
router.register(
    r"draft-experiments",
    NimbusExperimentDraftViewSet,
    "nimbus-experiment-rest-v8-draft",
)
urlpatterns = router.urls
