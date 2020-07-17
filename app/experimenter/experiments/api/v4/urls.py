from rest_framework.routers import SimpleRouter
from experimenter.experiments.api.v4.views import ExperimentRapidDetailsView


router = SimpleRouter()
router.register(r"experiments", ExperimentRapidDetailsView, "experiment-rapid-recipe")
urlpatterns = router.urls

