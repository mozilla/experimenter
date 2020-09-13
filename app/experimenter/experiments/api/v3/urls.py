from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v3.views import ExperimentRapidViewSet

router = SimpleRouter()
router.register(r"experiments", ExperimentRapidViewSet, "experiments-rapid")
urlpatterns = router.urls
