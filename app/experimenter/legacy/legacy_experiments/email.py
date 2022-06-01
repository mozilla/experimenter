import logging

from django.conf import settings
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string

from experimenter.legacy.legacy_experiments.constants import ExperimentConstants
from experimenter.legacy.legacy_experiments.models import Experiment, ExperimentEmail


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
            "locales": [str(locale) for locale in experiment.locales.all()],
            "countries": [str(country) for country in experiment.countries.all()],
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


def send_experiment_comment_email(comment):
    experiment = comment.experiment
    subject = Experiment.COMMENT_EMAIL_SUBJECT.format(
        comment=comment, experiment=experiment
    )
    format_and_send_html_email(
        comment.experiment,
        "experiments/emails/new_comment_email.html",
        {
            "experiment": comment.experiment,
            "comment": comment,
        },
        subject,
        Experiment.EXPERIMENT_COMMENT,
    )


def send_experiment_change_email(change):

    # Launch has its own separate email
    if change != "Launched Experiment":
        subject = Experiment.CHANGE_EMAIL_SUBJECT.format(change=change)
        format_and_send_html_email(
            change.experiment,
            "experiments/emails/new_change_email.html",
            {"change": change},
            subject,
            Experiment.EXPERIMENT_EDIT,
        )


def format_and_send_html_email(
    experiment, file_string, template_vars, subject, email_type, cc_recipients=None
):
    content = render_to_string(file_string, template_vars)

    version = experiment.format_firefox_versions
    channel = experiment.firefox_channel

    recipients = [experiment.owner.email] + list(
        experiment.subscribers.values_list("email", flat=True)
    )

    if experiment.analysis_owner:
        recipients.append(experiment.analysis_owner)

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


def send_period_ending_emails_task(experiment):
    # send experiment ending soon emails if end date is 5 days out
    if experiment.ending_soon:
        if not ExperimentEmail.objects.filter(
            experiment=experiment, type=ExperimentConstants.EXPERIMENT_ENDS
        ).exists():
            send_experiment_ending_email(experiment)
            logging.info("Sent ending email for Experiment: {}".format(experiment))
    # send enrollment ending emails if enrollment end
    # date is 5 days out
    if experiment.enrollment_end_date and experiment.enrollment_ending_soon:
        if not ExperimentEmail.objects.filter(
            experiment=experiment, type=ExperimentConstants.EXPERIMENT_PAUSES
        ).exists():
            send_enrollment_pause_email(experiment)
            logging.info(
                "Sent enrollment pause email for Experiment: {}".format(experiment)
            )
