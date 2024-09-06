from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v8.views import (
    NimbusExperimentDraftViewSet,
    NimbusExperimentViewSet,
)

router = SimpleRouter()
router.register(r"experiments", NimbusExperimentViewSet, "nimbus-experiment-rest-v8")
router.register(
    r"draft-experiments",
    NimbusExperimentDraftViewSet,
    "nimbus-experiment-rest-v8-draft",
)
urlpatterns = router.urls
