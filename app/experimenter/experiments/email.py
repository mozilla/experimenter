from django.conf import settings
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string

from experimenter.experiments.models import Experiment


def send_intent_to_ship_email(experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)

    bug_url = settings.BUGZILLA_DETAIL_URL.format(id=experiment.bugzilla_id)

    # Because that's how it's done in Experiment.population (property)
    percent_of_population = f"{float(experiment.population_percent):g}%"

    content = render_to_string(
        "experiments/intent_to_ship.txt",
        {
            "experiment": experiment,
            "bug_url": bug_url,
            "percent_of_population": percent_of_population,
            "locales": [str(l) for l in experiment.locales.all()],
            "countries": [str(c) for c in experiment.countries.all()],
        },
    )
    # Strip extra newlines from autoescape tag
    content = content.strip() + "\n"

    channel = experiment.firefox_channel
    email = EmailMessage(
        Experiment.INTENT_TO_SHIP_EMAIL_SUBJECT.format(
            name=experiment.name,
            version=experiment.format_firefox_versions,
            channel=channel,
        ),
        content,
        settings.EMAIL_SENDER,
        [settings.EMAIL_RELEASE_DRIVERS],
        cc=[experiment.owner.email],
    )
    email.send(fail_silently=False)


def send_experiment_launch_email(experiment):

    content = render_to_string(
        "experiments/launch_experiment_email.txt", {"experiment": experiment}
    )

    version = experiment.format_firefox_versions
    channel = experiment.firefox_channel

    email = EmailMessage(
        Experiment.LAUNCH_EMAIL_SUBJECT.format(
            name=experiment.name, version=version, channel=channel
        ),
        content,
        settings.EMAIL_SENDER,
        [settings.EMAIL_RELEASE_DRIVERS],
        cc=[experiment.owner.email],
    )

    email.send(fail_silently=False)
