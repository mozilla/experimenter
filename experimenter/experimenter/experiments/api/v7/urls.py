from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v7.views import NimbusExperimentViewSet

router = SimpleRouter()
router.register(r"experiments", NimbusExperimentViewSet, "nimbus-experiment-rest-v7")

urlpatterns = router.urls
