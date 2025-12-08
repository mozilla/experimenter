from django.conf import settings
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusEmail, NimbusExperiment


def nimbus_send_experiment_ending_email(experiment):
    nimbus_format_and_send_html_email(
        experiment,
        "emails/experiment_ending_email.html",
        {
            "experiment": experiment,
        },
        NimbusExperiment.EMAIL_EXPERIMENT_END_SUBJECT,
        NimbusExperiment.EmailType.EXPERIMENT_END,
    )


def nimbus_send_enrollment_ending_email(experiment):
    nimbus_format_and_send_html_email(
        experiment,
        "emails/enrollment_ending_email.html",
        {
            "experiment": experiment,
        },
        NimbusExperiment.EMAIL_ENROLLMENT_END_SUBJECT,
        NimbusExperiment.EmailType.ENROLLMENT_END,
    )


def nimbus_format_and_send_html_email(
    experiment, file_string, template_vars, subject, email_type
):
    content = render_to_string(file_string, template_vars)

    all_emails = experiment.notification_emails
    owner_email = experiment.owner.email
    cc_emails = [email for email in all_emails if email != owner_email]

    email = EmailMessage(
        subject.format(name=experiment.name),
        content,
        settings.EMAIL_SENDER,
        [owner_email],
        cc=cc_emails,
    )

    email.content_subtype = "html"
    email.send(fail_silently=False)

    from experimenter.slack.tasks import nimbus_send_slack_notification

    action_text = NimbusConstants.SLACK_EMAIL_ACTIONS.get(email_type, "has updates")
    nimbus_send_slack_notification.delay(
        experiment_id=experiment.id,
        email_addresses=experiment.notification_emails,
        action_text=action_text,
    )

    NimbusEmail.objects.create(experiment=experiment, type=email_type)
