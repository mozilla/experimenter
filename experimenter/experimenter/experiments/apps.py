import markus
import sentry_sdk
from django.apps import AppConfig
from django.conf import settings
from sentry_sdk.integrations.django import DjangoIntegration

from experimenter.base import app_version


class ExperimentsConfig(AppConfig):
    name = "experimenter.experiments"

    def ready(self):
        markus.configure(settings.MARKUS_BACKEND)

        if settings.SENTRY_DSN:  # pragma: no cover
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[DjangoIntegration()],
                # Set traces_sample_rate to 1.0 to capture 100%
                # of transactions for performance monitoring.
                # We recommend adjusting this value in production.
                traces_sample_rate=1.0,
                # If you wish to associate users to errors (assuming you are using
                # django.contrib.auth) you may enable sending PII data.
                send_default_pii=False,
                environment=settings.SENTRY_ENV,
                release=app_version(),
            )
