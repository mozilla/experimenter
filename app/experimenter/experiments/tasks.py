from smtplib import SMTPException

from django.conf import settings
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.experiments import email, bugzilla
from experimenter.experiments.models import Experiment
from experimenter.notifications.models import Notification


logger = get_task_logger(__name__)


NOTIFICATION_MESSAGE_REVIEW_EMAIL = "An email was sent to {email} about {name}"
NOTIFICATION_MESSAGE_CREATE_BUG = (
    'A <a target="_blank" href="{bug_url}">Bugzilla '
    "Ticket</a> was created for this experiment"
)
NOTIFICATION_MESSAGE_ADD_COMMENT = (
    'The <a target="_blank" href="{bug_url}">Bugzilla '
    "Ticket</a> was updated with the details "
    "of this experiment"
)


@app.task
def send_review_email_task(
    user_id, experiment_name, experiment_url, needs_attention
):
    logger.info("Sending email")

    try:
        email.send_review_email(
            experiment_name, experiment_url, needs_attention
        )
        logger.info("Email sent")

        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_REVIEW_EMAIL.format(
                email=settings.EMAIL_REVIEW, name=experiment_name
            ),
        )
    except SMTPException:
        logger.error("Failed to send email")


@app.task
def create_experiment_bug_task(user_id, experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)

    logger.info("Creating Bugzilla ticket")
    bugzilla_id = bugzilla.create_experiment_bug(experiment)

    if bugzilla_id is not None:
        logger.info("Bugzilla ticket created")
        experiment.bugzilla_id = bugzilla_id
        experiment.save()

        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_CREATE_BUG.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        logger.info("Bugzilla ticket notification sent")


@app.task
def add_experiment_comment_task(user_id, experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)

    logger.info("Updating Bugzilla comment")
    comment_id = bugzilla.add_experiment_comment(experiment)

    if comment_id is not None:
        logger.info("Bugzilla comment updated")
        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_ADD_COMMENT.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        logger.info("Bugzilla comment notification sent")
