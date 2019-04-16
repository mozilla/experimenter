from django.apps import AppConfig
from django.conf import settings

import markus


class ExperimentsConfig(AppConfig):
    name = "experimenter.experiments"

    def ready(self):
        markus.configure(settings.MARKUS_BACKEND)
