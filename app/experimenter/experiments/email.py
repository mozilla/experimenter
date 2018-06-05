from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail


def send_review_email(experiment, needs_attention):
    attention = experiment.ATTENTION_MESSAGE if needs_attention else ""

    content = experiment.REVIEW_EMAIL_TEMPLATE.format(
        experiment_url=urljoin(
            "https://{}".format(settings.HOSTNAME),
            experiment.get_absolute_url(),
        ),
        attention=attention,
    )

    send_mail(
        experiment.REVIEW_EMAIL_SUBJECT.format(name=experiment.name),
        content,
        settings.EMAIL_SENDER,
        [settings.EMAIL_REVIEW],
        fail_silently=False,
    )
