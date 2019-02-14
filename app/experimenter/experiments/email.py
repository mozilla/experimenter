from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail

from experimenter.experiments.models import Experiment


def send_review_email(experiment_name, experiment_url, needs_attention):
    attention = Experiment.ATTENTION_MESSAGE if needs_attention else ""

    content = Experiment.REVIEW_EMAIL_TEMPLATE.format(
        experiment_url=urljoin(
            "https://{}".format(settings.HOSTNAME), experiment_url
        ),
        attention=attention,
    )
    send_mail(
        Experiment.REVIEW_EMAIL_SUBJECT.format(name=experiment_name),
        content,
        settings.EMAIL_SENDER,
        [settings.EMAIL_REVIEW],
        fail_silently=False,
    )
