from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v6.views import NimbusExperimentViewSet

router = SimpleRouter()
router.register(r"experiments", NimbusExperimentViewSet, "nimbus-experiment-rest")
urlpatterns = router.urls
