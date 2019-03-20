from django.apps import AppConfig

from experimenter.base.checks import register


class BaseAppConfig(AppConfig):
    name = "experimenter.base"

    def ready(self):
        register()
