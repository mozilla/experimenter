from rest_framework.routers import SimpleRouter, Route

from experimenter.experiments.api.v3.views import ExperimentRapidViewSet


class ExperimentRapidRouter(SimpleRouter):
    routes = [
        # List route.
        Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={"post": "create"},
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        # Detail route.
        Route(
            url=r"^{prefix}/{lookup}{trailing_slash}$",
            mapping={"get": "retrieve", "put": "update"},
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
    ]


router = ExperimentRapidRouter()
router.register(r"experiments", ExperimentRapidViewSet, "experiments-rapid")

urlpatterns = router.urls
