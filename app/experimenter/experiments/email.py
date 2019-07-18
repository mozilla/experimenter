from django.conf import settings
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string

from experimenter.experiments.models import Experiment, ExperimentEmail
from experimenter.experiments.constants import ExperimentConstants


def send_intent_to_ship_email(experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)

    bug_url = settings.BUGZILLA_DETAIL_URL.format(id=experiment.bugzilla_id)

    # Because that's how it's done in Experiment.population (property)
    percent_of_population = f"{float(experiment.population_percent):g}%"

    format_and_send_html_email(
        experiment,
        "experiments/emails/intent_to_ship.html",
        {
            "experiment": experiment,
            "bug_url": bug_url,
            "percent_of_population": percent_of_population,
            "locales": [str(l) for l in experiment.locales.all()],
            "countries": [str(c) for c in experiment.countries.all()],
        },
        Experiment.INTENT_TO_SHIP_EMAIL_SUBJECT,
        Experiment.INTENT_TO_SHIP_EMAIL_LABEL,
        cc_recipients=[settings.EMAIL_RELEASE_DRIVERS],
    )


def send_experiment_launch_email(experiment):
    format_and_send_html_email(
        experiment,
        "experiments/emails/launch_experiment_email.html",
        {
            "experiment": experiment,
            "change_window_url": ExperimentConstants.NORMANDY_CHANGE_WINDOW,
        },
        Experiment.LAUNCH_EMAIL_SUBJECT,
        Experiment.EXPERIMENT_STARTS,
    )


def send_experiment_ending_email(experiment):

    format_and_send_html_email(
        experiment,
        "experiments/emails/experiment_ending_email.html",
        {
            "experiment": experiment,
            "change_window_url": ExperimentConstants.NORMANDY_CHANGE_WINDOW,
        },
        Experiment.ENDING_EMAIL_SUBJECT,
        Experiment.EXPERIMENT_ENDS,
    )


def send_enrollment_pause_email(experiment):

    format_and_send_html_email(
        experiment,
        "experiments/emails/enrollment_pause_email.html",
        {
            "experiment": experiment,
            "change_window_url": ExperimentConstants.NORMANDY_CHANGE_WINDOW,
        },
        Experiment.PAUSE_EMAIL_SUBJECT,
        Experiment.EXPERIMENT_PAUSES,
    )


def format_and_send_html_email(
    experiment,
    file_string,
    template_vars,
    subject,
    email_type,
    cc_recipients=None,
):
    content = render_to_string(file_string, template_vars)

    version = experiment.format_firefox_versions
    channel = experiment.firefox_channel

    recipients = [experiment.owner.email] + list(
        experiment.subscribers.values_list("email", flat=True)
    )

    email = EmailMessage(
        subject.format(name=experiment.name, version=version, channel=channel),
        content,
        settings.EMAIL_SENDER,
        recipients,
        cc=cc_recipients,
    )
    email.content_subtype = "html"

    email.send(fail_silently=False)

    ExperimentEmail.objects.create(experiment=experiment, type=email_type)
