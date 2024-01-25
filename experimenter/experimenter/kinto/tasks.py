import markus
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from experimenter.celery import app
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.email import (
    nimbus_send_enrollment_ending_email,
    nimbus_send_experiment_ending_email,
)
from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment
from experimenter.kinto.client import KintoClient

logger = get_task_logger(__name__)
metrics = markus.get_metrics("kinto.nimbus_tasks")


def get_kinto_user():
    user, _ = User.objects.get_or_create(
        email=settings.KINTO_DEFAULT_CHANGELOG_USER,
        username=settings.KINTO_DEFAULT_CHANGELOG_USER,
    )
    return user


@app.task
@metrics.timer_decorator("check_kinto_push_queue")
def nimbus_check_kinto_push_queue():
    """
    A scheduled task that passes each application to a new scheduled
    task for working with kinto
    """
    for collection in (
        settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
        settings.KINTO_COLLECTION_NIMBUS_MOBILE,
        settings.KINTO_COLLECTION_NIMBUS_WEB,
    ):
        nimbus_check_kinto_push_queue_by_collection.delay(collection)


@app.task
@metrics.timer_decorator("check_kinto_push_queue_by_application")
def nimbus_check_kinto_push_queue_by_collection(collection):
    """
    Because kinto has a restriction that it can only have a single pending review, this
    task brokers the queue of all experiments ready to be pushed to kinto and ensures
    that only a single experiment is ever in review.

    A scheduled task that
    - Checks the kinto collection for a single rejected experiment from a previous push
       - If one exists, pull it out of the collection and mark it as rejected
    - Checks if there is still a pending review and if so, aborts
    - Gets the list of all experiments ready to be pushed to kinto and pushes the first
      one
    - Checks for experiments that should be paused but are not paused in the kinto
      collection and marks them as paused and updates the record in the collection.
    """
    metrics.incr(f"check_kinto_push_queue_by_collection:{collection}.started")
    applications = [
        application.slug
        for application in NimbusExperiment.APPLICATION_CONFIGS.values()
        if application.kinto_collection == collection
    ]
    kinto_client = KintoClient(collection)

    should_rollback = False
    if kinto_client.has_pending_review():
        logger.info(f"{collection} has pending review")
        if handle_pending_review(applications):
            return

        should_rollback = True

    if kinto_client.has_rejection():
        logger.info(f"{collection} has rejection")
        handle_rejection(applications, kinto_client)
        should_rollback = True

    if should_rollback:
        kinto_client.rollback_changes()

    records = kinto_client.get_main_records()
    handle_launching_experiments(applications, records)
    handle_updating_experiments(applications, records)
    handle_ending_experiments(applications, records)
    handle_waiting_experiments(applications)

    if queued_launch_experiment := NimbusExperiment.objects.launch_queue(
        applications
    ).first():
        nimbus_push_experiment_to_kinto.delay(collection, queued_launch_experiment.id)
    elif queued_end_experiment := NimbusExperiment.objects.end_queue(
        applications
    ).first():
        nimbus_end_experiment_in_kinto.delay(collection, queued_end_experiment.id)
    elif queued_pause_experiment := NimbusExperiment.objects.update_queue(
        applications
    ).first():
        nimbus_update_experiment_in_kinto.delay(collection, queued_pause_experiment.id)

    metrics.incr(f"check_kinto_push_queue_by_collection:{collection}.completed")


def handle_pending_review(applications):
    if experiment := NimbusExperiment.objects.waiting(applications).first():
        if experiment.should_timeout:
            experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
            if experiment.status == experiment.Status.DRAFT:
                experiment.published_date = None
            experiment.save()

            generate_nimbus_changelog(
                experiment,
                get_kinto_user(),
                message=NimbusChangeLog.Messages.TIMED_OUT_IN_KINTO,
            )

            logger.info(f"{experiment.slug} timed out")
        else:
            # There is a pending review but it shouldn't time out
            return True


def handle_rejection(applications, kinto_client):
    collection_data = kinto_client.get_rejected_collection_data()
    if experiment := NimbusExperiment.objects.waiting(applications).first():
        if (
            experiment.is_rollout is True
            and experiment.status == NimbusExperiment.Status.LIVE
            and (
                experiment.status_next
                in (NimbusExperiment.Status.LIVE, NimbusExperiment.Status.COMPLETE)
            )
            and experiment.is_paused is False
        ):
            experiment.is_rollout_dirty = True

        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.status_next = None
        experiment.is_paused = False
        if experiment.status == experiment.Status.DRAFT:
            experiment.published_date = None
        experiment.save()

        generate_nimbus_changelog(
            experiment,
            get_kinto_user(),
            message=collection_data["last_reviewer_comment"],
        )

        logger.info(f"{experiment.slug} rejected")


def handle_launching_experiments(applications, records):
    for experiment in NimbusExperiment.objects.waiting_to_launch_queue(applications):
        if experiment.slug in records:
            logger.info(
                f"{experiment} status is being updated to live".format(
                    experiment=experiment
                )
            )

            published_record = records[experiment.slug].copy()
            published_record.pop("last_modified")

            experiment.status = NimbusExperiment.Status.LIVE
            experiment.status_next = None
            experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
            experiment.published_dto = published_record
            experiment.save()

            generate_nimbus_changelog(
                experiment,
                get_kinto_user(),
                message=NimbusChangeLog.Messages.LIVE,
            )

            logger.info(f"{experiment.slug} launched")


def handle_updating_experiments(applications, records):
    for experiment in NimbusExperiment.objects.waiting_to_update_queue(applications):
        published_record = records.get(experiment.slug).copy()
        published_record.pop("last_modified")

        if experiment.published_dto is None:
            continue

        stored_record = experiment.published_dto.copy()
        stored_record.pop("last_modified", None)

        if published_record != stored_record:
            logger.info(f"{experiment} is updated in Kinto".format(experiment=experiment))
            experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
            experiment.status_next = None
            experiment.published_dto = published_record
            experiment.is_rollout_dirty = False
            experiment.save()

            generate_nimbus_changelog(
                experiment,
                get_kinto_user(),
                message=NimbusChangeLog.Messages.UPDATED_IN_KINTO,
            )

            logger.info(f"{experiment.slug} updated")


def handle_ending_experiments(applications, records):
    for experiment in NimbusExperiment.objects.waiting_to_end_queue(applications):
        if experiment.slug not in records:
            logger.info(
                f"{experiment.slug} status is being updated to complete".format(
                    experiment=experiment
                )
            )

            experiment.status = NimbusExperiment.Status.COMPLETE
            experiment.status_next = None
            experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
            experiment.is_rollout_dirty = False
            experiment.save()

            generate_nimbus_changelog(
                experiment,
                get_kinto_user(),
                message=NimbusChangeLog.Messages.COMPLETED,
            )

            logger.info(f"{experiment.slug} ended")


def handle_waiting_experiments(applications):
    waiting_experiments = NimbusExperiment.objects.filter(
        publish_status=NimbusExperiment.PublishStatus.WAITING,
        application__in=applications,
    )
    for experiment in waiting_experiments:
        experiment.status_next = None
        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        if experiment.status == experiment.Status.DRAFT:
            experiment.published_date = None
        experiment.save()

        generate_nimbus_changelog(
            experiment,
            get_kinto_user(),
            message=NimbusChangeLog.Messages.REJECTED_FROM_KINTO,
        )

        logger.info(f"{experiment.slug} rejected without reason(rollback)")


@app.task
@metrics.timer_decorator("push_experiment_to_kinto.timing")
def nimbus_push_experiment_to_kinto(collection, experiment_id):
    """
    An invoked task that given a single experiment id, query it in the db, serialize it,
    and push its data to the configured collection. If it fails for any reason, log the
    error and reraise it so it will be forwarded to sentry.
    """

    metrics.incr("push_experiment_to_kinto.started")

    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        logger.info(f"Pushing {experiment.slug} to Kinto")

        kinto_client = KintoClient(collection)

        if (
            experiment.published_date is None
            or experiment.status == experiment.Status.DRAFT
        ):
            experiment.published_date = timezone.now()

        data = NimbusExperimentSerializer(experiment).data

        kinto_client.create_record(data)

        experiment.publish_status = NimbusExperiment.PublishStatus.WAITING
        experiment.save()

        generate_nimbus_changelog(
            experiment,
            get_kinto_user(),
            message=NimbusChangeLog.Messages.LAUNCHING_TO_KINTO,
        )

        logger.info(f"{experiment.slug} pushed to Kinto")
        metrics.incr("push_experiment_to_kinto.completed")
    except Exception as e:
        metrics.incr("push_experiment_to_kinto.failed")
        logger.info(f"Pushing experiment {experiment_id} to Kinto failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("update_experiment_in_kinto")
def nimbus_update_experiment_in_kinto(collection, experiment_id):
    """
    An invoked task that given a single experiment id, reserializes
    and updates the record. If it fails for any reason, log the error and
    reraise it so it will be forwarded to sentry.
    """
    metrics.incr("update_experiment_in_kinto.started")

    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        logger.info(f"Updating {experiment.slug} in Kinto")

        kinto_client = KintoClient(collection)

        data = NimbusExperimentSerializer(experiment).data

        kinto_client.update_record(data)

        experiment.publish_status = NimbusExperiment.PublishStatus.WAITING
        experiment.save()

        generate_nimbus_changelog(
            experiment,
            get_kinto_user(),
            message=NimbusChangeLog.Messages.UPDATING_IN_KINTO,
        )

        logger.info(f"{experiment.slug} updated in Kinto")

        metrics.incr("update_experiment_in_kinto.completed")
    except Exception as e:
        metrics.incr("update_experiment_in_kinto.failed")
        logger.info(f"Updating experiment {experiment_id} in Kinto failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("end_experiment_in_kinto")
def nimbus_end_experiment_in_kinto(collection, experiment_id):
    """
    An invoked task that given a single experiment id, delete its data from
    the configured collection. If it fails for any reason, log the error and
    reraise it so it will be forwarded to sentry.
    """
    metrics.incr("end_experiment_in_kinto.started")

    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        logger.info(f"Deleting {experiment.slug} from Kinto")

        kinto_client = KintoClient(collection)
        kinto_client.delete_record(experiment.slug)

        experiment.publish_status = NimbusExperiment.PublishStatus.WAITING
        experiment.save()

        generate_nimbus_changelog(
            experiment,
            get_kinto_user(),
            message=NimbusChangeLog.Messages.DELETING_FROM_KINTO,
        )

        logger.info(f"{experiment.slug} deleted from Kinto")
        metrics.incr("end_experiment_in_kinto.completed")
    except Exception as e:
        metrics.incr("end_experiment_in_kinto.failed")
        logger.info(f"Deleting experiment {experiment_id} from Kinto failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("nimbus_synchronize_preview_experiments_in_kinto")
def nimbus_synchronize_preview_experiments_in_kinto():
    """
    A scheduled task that pushes any experiments with status PREVIEW to the preview
    collection and removes any experiments not with status PREVIEW from the preview
    collection.
    """
    metrics.incr("nimbus_synchronize_preview_experiments_in_kinto.started")

    kinto_client = KintoClient(settings.KINTO_COLLECTION_NIMBUS_PREVIEW, review=False)

    try:
        published_preview_slugs = kinto_client.get_main_records().keys()

        should_publish_experiments = NimbusExperiment.objects.filter(
            status=NimbusExperiment.Status.PREVIEW
        ).exclude(slug__in=published_preview_slugs)

        for experiment in should_publish_experiments:
            data = NimbusExperimentSerializer(experiment).data
            kinto_client.create_record(data)
            experiment.published_dto = data
            experiment.save()
            logger.info(f"{experiment.slug} is being pushed to preview")

        should_unpublish_experiments = NimbusExperiment.objects.filter(
            slug__in=published_preview_slugs
        ).exclude(status=NimbusExperiment.Status.PREVIEW)

        for experiment in should_unpublish_experiments:
            kinto_client.delete_record(experiment.slug)
            logger.info(f"{experiment.slug} is being removed from preview")

        metrics.incr("nimbus_synchronize_preview_experiments_in_kinto.completed")

    except Exception as e:
        metrics.incr("nimbus_synchronize_preview_experiments_in_kinto.failed")
        logger.info(f"Synchronizing preview experiments failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("nimbus_send_emails")
def nimbus_send_emails():
    """
    A scheduled task that checks for any experiments that
    should end enrollment or end the experiment and sends
    a reminder email
    """
    metrics.incr("nimbus_send_emails.started")

    experiments = NimbusExperiment.objects.filter(
        status=NimbusExperiment.Status.LIVE,
    )

    for experiment in experiments:
        if (
            experiment.should_end_enrollment
            and not experiment.is_rollout
            and not experiment.emails.filter(
                type=NimbusExperiment.EmailType.ENROLLMENT_END
            ).exists()
        ):
            nimbus_send_enrollment_ending_email(experiment)
            logger.info(f"{experiment} end enrollment email sent")

        if (
            experiment.should_end
            and not experiment.emails.filter(
                type=NimbusExperiment.EmailType.EXPERIMENT_END
            ).exists()
        ):
            nimbus_send_experiment_ending_email(experiment)
            logger.info(f"{experiment} end email sent")

    metrics.incr("nimbus_send_emails.completed")
