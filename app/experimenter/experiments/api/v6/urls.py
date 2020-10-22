from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v6.views import (
    NimbusExperimentViewSet,
    NimbusProbeSetViewSet,
)

router = SimpleRouter()
router.register(r"experiments", NimbusExperimentViewSet, "nimbus-experiment-rest")
router.register(r"probesets", NimbusProbeSetViewSet, "nimbus-probeset-rest")
urlpatterns = router.urls
