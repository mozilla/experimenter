from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v6.views import (
    NimbusExperimentFirstRunViewSet,
    NimbusExperimentViewSet,
)

router = SimpleRouter()
router.register(r"experiments", NimbusExperimentViewSet, "nimbus-experiment-rest")
router.register(
    r"experiments-first-run",
    NimbusExperimentFirstRunViewSet,
    "nimbus-experiment-rest-first-run",
)
urlpatterns = router.urls
