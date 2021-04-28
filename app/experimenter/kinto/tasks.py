import markus
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model

from experimenter.celery import app
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.email import nimbus_send_experiment_ending_email
from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment
from experimenter.kinto.client import KintoClient

logger = get_task_logger(__name__)
metrics = markus.get_metrics("kinto.nimbus_tasks")


def get_kinto_user():
    user, _ = get_user_model().objects.get_or_create(
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
    for collection in NimbusExperiment.KINTO_COLLECTION_APPLICATIONS.keys():
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
    applications = NimbusExperiment.KINTO_COLLECTION_APPLICATIONS[collection]
    kinto_client = KintoClient(collection)

    should_rollback = False
    if kinto_client.has_pending_review():
        logger.info(f"{collection} has pending review")
        should_abort = handle_pending_review(applications, kinto_client)

        if should_abort:
            return

        should_rollback = True

    if kinto_client.has_rejection():
        logger.info(f"{collection} has rejection")
        handle_rejection(applications, kinto_client)
        should_rollback = True

    if should_rollback:
        kinto_client.rollback_changes()

    if queued_launch_experiment := NimbusExperiment.objects.launch_queue(
        applications
    ).first():
        nimbus_push_experiment_to_kinto.delay(collection, queued_launch_experiment.id)
    elif queued_end_experiment := NimbusExperiment.objects.end_queue(
        applications
    ).first():
        nimbus_end_experiment_in_kinto.delay(collection, queued_end_experiment.id)
    elif queued_pause_experiment := NimbusExperiment.objects.pause_queue(
        applications
    ).first():
        nimbus_pause_experiment_in_kinto.delay(collection, queued_pause_experiment.id)

    metrics.incr(f"check_kinto_push_queue_by_collection:{collection}.completed")


def handle_pending_review(applications, kinto_client):
    experiment = NimbusExperiment.objects.waiting(applications).first()

    if experiment:
        if experiment.has_filter(experiment.Filters.SHOULD_TIMEOUT):
            experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
            experiment.is_end_requested = False
            experiment.save()

            generate_nimbus_changelog(
                experiment,
                get_kinto_user(),
                message=NimbusChangeLog.Messages.TIMED_OUT_IN_KINTO,
            )

            logger.info(f"{experiment} timed out")
        else:
            # There is a pending review but it shouldn't time out
            return True


def handle_rejection(applications, kinto_client):
    collection_data = kinto_client.get_rejected_collection_data()
    experiment = NimbusExperiment.objects.waiting(applications).first()

    if experiment:
        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.is_end_requested = False
        experiment.save()

        generate_nimbus_changelog(
            experiment,
            get_kinto_user(),
            message=collection_data["last_reviewer_comment"],
        )

        logger.info(f"{experiment} rejected")


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

        data = NimbusExperimentSerializer(experiment).data

        kinto_client.create_record(data)

        experiment.publish_status = NimbusExperiment.PublishStatus.WAITING
        experiment.save()

        generate_nimbus_changelog(
            experiment,
            get_kinto_user(),
            message=NimbusChangeLog.Messages.PUSHED_TO_KINTO,
        )

        logger.info(f"{experiment.slug} pushed to Kinto")
        metrics.incr("push_experiment_to_kinto.completed")
    except Exception as e:
        metrics.incr("push_experiment_to_kinto.failed")
        logger.info(f"Pushing experiment {experiment.slug} to Kinto failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("pause_experiment_in_kinto")
def nimbus_pause_experiment_in_kinto(collection, experiment_id):
    """
    An invoked task that given a single experiment id, marks it as paused
    and updates the record. If it fails for any reason, log the error and
    reraise it so it will be forwarded to sentry.
    """
    metrics.incr("pause_experiment_in_kinto.started")

    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        logger.info(f"Deleting {experiment.slug} from Kinto")

        kinto_client = KintoClient(collection)

        record = kinto_client.get_main_records()[experiment.slug]

        if not record["isEnrollmentPaused"]:
            data = NimbusExperimentSerializer(experiment).data
            data["isEnrollmentPaused"] = True

            kinto_client.update_record(data)

            experiment.publish_status = NimbusExperiment.PublishStatus.WAITING
            experiment.save()

            logger.info(f"{experiment.slug} paused in Kinto")

        metrics.incr("pause_experiment_in_kinto.completed")
    except Exception as e:
        metrics.incr("pause_experiment_in_kinto.failed")
        logger.info(f"Pausing experiment id {experiment.slug} in Kinto failed: {e}")
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
            message=NimbusChangeLog.Messages.DELETED_FROM_KINTO,
        )

        logger.info(f"{experiment.slug} deleted from Kinto")
        metrics.incr("end_experiment_in_kinto.completed")
    except Exception as e:
        metrics.incr("end_experiment_in_kinto.failed")
        logger.info(f"Deleting experiment id {experiment.slug} from Kinto failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("check_experiments_are_live")
def nimbus_check_experiments_are_live():
    """
    A scheduled task that checks the kinto collection for any experiment slugs that are
    present in the collection but are not yet marked as live in the database and marks
    them as live.
    """
    metrics.incr("check_experiments_are_live.started")

    for collection in NimbusExperiment.KINTO_COLLECTION_APPLICATIONS.keys():
        kinto_client = KintoClient(collection)
        records = kinto_client.get_main_records()

        for experiment in NimbusExperiment.objects.waiting_to_launch_queue():
            if experiment.slug in records:
                logger.info(
                    f"{experiment} status is being updated to live".format(
                        experiment=experiment
                    )
                )

                experiment.status = NimbusExperiment.Status.LIVE
                experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
                experiment.save()

                generate_nimbus_changelog(
                    experiment,
                    get_kinto_user(),
                    message=NimbusChangeLog.Messages.LIVE,
                )

                logger.info(f"{experiment.slug} status is set to Live")

    metrics.incr("check_experiments_are_live.completed")


@app.task
@metrics.timer_decorator("check_experiments_are_paused")
def nimbus_check_experiments_are_paused():
    """
    A scheduled task that checks the kinto collection for any experiment slugs that are
    marked as enrollment paused in the collection but not in the database, and update them
    in the database accordingly.
    """
    metrics.incr("check_experiments_are_paused.started")

    for (
        collection,
        applications,
    ) in NimbusExperiment.KINTO_COLLECTION_APPLICATIONS.items():
        kinto_client = KintoClient(collection)
        records = kinto_client.get_main_records()

        pause_queue = NimbusExperiment.objects.filter(
            NimbusExperiment.Filters.IS_PAUSE_QUEUED,
            application__in=applications,
        )

        for experiment in pause_queue:
            if records[experiment.slug]["isEnrollmentPaused"]:
                logger.info(
                    f"{experiment.slug} is_paused is being updated to True".format(
                        experiment=experiment
                    )
                )

                experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
                experiment.is_paused = True
                experiment.save()

                generate_nimbus_changelog(
                    experiment,
                    get_kinto_user(),
                    message=NimbusChangeLog.Messages.PAUSED,
                )

                logger.info(f"{experiment.slug} is_paused is set to True")

    metrics.incr("check_experiments_are_paused.completed")


@app.task
@metrics.timer_decorator("check_experiments_are_complete")
def nimbus_check_experiments_are_complete():
    """
    A scheduled task that checks the kinto collection for any experiment slugs that are
    marked as live in the database but missing from the collection, indicating that they
    are no longer live and can be marked as complete.
    """
    metrics.incr("check_experiments_are_complete.started")

    for (
        collection,
        applications,
    ) in NimbusExperiment.KINTO_COLLECTION_APPLICATIONS.items():
        kinto_client = KintoClient(collection)

        live_experiments = NimbusExperiment.objects.filter(
            status=NimbusExperiment.Status.LIVE,
            application__in=applications,
        )

        records = kinto_client.get_main_records()

        for experiment in live_experiments:
            if (
                experiment.should_end
                and not experiment.emails.filter(
                    type=NimbusExperiment.EmailType.EXPERIMENT_END
                ).exists()
            ):
                nimbus_send_experiment_ending_email(experiment)

            if experiment.slug not in records:
                logger.info(
                    f"{experiment.slug} status is being updated to complete".format(
                        experiment=experiment
                    )
                )

                experiment.status = NimbusExperiment.Status.COMPLETE
                experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
                experiment.save()

                generate_nimbus_changelog(
                    experiment,
                    get_kinto_user(),
                    message=NimbusChangeLog.Messages.COMPLETED,
                )

                logger.info(f"{experiment.slug} status is set to Complete")

    metrics.incr("check_experiments_are_complete.completed")


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
