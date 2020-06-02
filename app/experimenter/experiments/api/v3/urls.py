from rest_framework import routers

from experimenter.experiments.api.v3.views import ExperimentRapidViewSet

router = routers.SimpleRouter()
router.register(r"experiments", ExperimentRapidViewSet, "experiments-rapid")

urlpatterns = router.urls
