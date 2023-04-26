import markus
from django.apps import AppConfig
from django.conf import settings
from django.core.checks import register as check_register

from experimenter.kinto.checks import remote_settings_check


class ExperimentsConfig(AppConfig):
    name = "experimenter.experiments"

    def ready(self):
        markus.configure(settings.MARKUS_BACKEND)

        check_register(remote_settings_check)
