from django.conf import settings
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string

from experimenter.experiments.models import NimbusEmail, NimbusExperiment


def nimbus_send_experiment_ending_email(experiment):
    nimbus_format_and_send_html_email(
        experiment,
        "nimbus/emails/experiment_ending_email.html",
        {
            "experiment": experiment,
        },
        NimbusExperiment.EMAIL_EXPERIMENT_END_SUBJECT,
        NimbusExperiment.EmailType.EXPERIMENT_END,
    )


def nimbus_send_enrollment_ending_email(experiment):
    nimbus_format_and_send_html_email(
        experiment,
        "nimbus/emails/enrollment_ending_email.html",
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

    email = EmailMessage(
        subject.format(name=experiment.name),
        content,
        settings.EMAIL_SENDER,
        [experiment.owner.email],
        cc=experiment.subscribers.all().values_list("email", flat=True),
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)

    NimbusEmail.objects.create(experiment=experiment, type=email_type)
