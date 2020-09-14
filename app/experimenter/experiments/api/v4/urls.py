from rest_framework.routers import SimpleRouter

from experimenter.experiments.api.v4.views import ExperimentRapidViewSet

router = SimpleRouter()
router.register(r"experiments", ExperimentRapidViewSet, "experiment-rapid-recipe")
urlpatterns = router.urls
