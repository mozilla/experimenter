import markus
from celery.utils.log import get_task_logger
from dateutil import parser
from django.utils import timezone

from experimenter.celery import app
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.models.nimbus import NimbusChangeLog, NimbusExperiment
from experimenter.normandy import client as normandy
from experimenter.reporting.models import ReportLog

logger = get_task_logger(__name__)
metrics = markus.get_metrics("experiments.tasks")


@app.task
@metrics.timer_decorator("generate_reportlogs.timing")
def generate_reportlogs():
    metrics.incr("generate_reportlogs.started")
    logger.info("Generating Reportlogs")

    last_log_date = get_latest_log_date()
    nimbus_changelogs = NimbusChangeLog.objects.filter(changed_on__gt=last_log_date)
    legacy_changelogs = ExperimentChangeLog.objects.filter(changed_on__gt=last_log_date)
    live_experiments = Experiment.objects.filter(status=Experiment.STATUS_LIVE)

    for l_changelog in legacy_changelogs:
        create_reportlog(l_changelog)

    for n_changelog in nimbus_changelogs:
        create_reportlog(n_changelog)

    for experiment in live_experiments:
        create_reportlog_from_normandy_history(experiment)


def get_latest_log_date():
    if ReportLog.objects.count():
        return ReportLog.objects.latest("timestamp").timestamp
    return timezone.datetime.min


def create_reportlog(changelog):

    experiment = changelog.experiment
    type = get_experiment_type(experiment)
    timestamp = changelog.changed_on
    event = get_event_type(changelog)
    event_reason = get_event_reason(changelog, event)
    message = changelog.message if changelog.message else ""

    if event and not is_duplicate_recipe_change(timestamp, experiment, event_reason):
        event_reason = get_event_reason(changelog, event)
        report_log = ReportLog.objects.create(
            timestamp=timestamp,
            experiment_slug=experiment.slug,
            experiment_name=experiment.name,
            experiment_type=type,
            experiment_old_status=changelog.old_status,
            experiment_new_status=changelog.new_status,
            event=event,
            event_reason=event_reason,
            comment=message,
        )
        report_log.projects.set(experiment.projects.all())


def create_reportlog_from_normandy_history(experiment):

    history = normandy.get_history_list(experiment.normandy_id)
    # first normandy history is creation
    if len(history) > 1:
        for revision in history:
            timestamp = parser.parse(revision.get("updated"))
            event_reason = ReportLog.EventReason.RECIPE_CHANGE
            if ReportLog.objects.filter(
                timestamp__date=timestamp,
                experiment_name=experiment.name,
                event_reason=event_reason,
            ).exists():
                break
            else:
                type = get_experiment_type(experiment)
                event = ReportLog.Event.UPDATE
                message = ""
                report_log = ReportLog.objects.create(
                    timestamp=timestamp,
                    experiment_slug=experiment.slug,
                    experiment_name=experiment.name,
                    experiment_type=type,
                    experiment_old_status=Experiment.STATUS_LIVE,
                    experiment_new_status=Experiment.STATUS_LIVE,
                    event=event,
                    event_reason=event_reason,
                    comment=message,
                )
                report_log.projects.set(experiment.projects.all())


def is_duplicate_recipe_change(date, experiment, event_reason):
    if event_reason == ReportLog.EventReason.RECIPE_CHANGE:
        return ReportLog.objects.filter(
            timestamp__date=date,
            experiment_name=experiment.name,
            event_reason=ReportLog.EventReason.RECIPE_CHANGE,
        ).exists()
    return False


def get_experiment_type(experiment):
    if type(experiment) == NimbusExperiment:
        application = experiment.application
        application_slug = NimbusConstants.APPLICATION_CONFIGS[application].slug
        return "Nimbus-{application}".format(application=application_slug.title())
    else:
        return "Normandy-{type}".format(type=experiment.type.title())


def get_event_type(changelog):
    if (
        changelog.old_status is None
        and changelog.new_status == ReportLog.ExperimentStatus.DRAFT
    ):
        return ReportLog.Event.CREATE
    if (
        changelog.old_status == ReportLog.ExperimentStatus.LIVE
        and changelog.new_status == ReportLog.ExperimentStatus.COMPLETE
    ):
        return ReportLog.Event.END
    if changelog.old_status != changelog.new_status or is_normandy_update(changelog):
        return ReportLog.Event.UPDATE


def is_normandy_update(changelog):
    return type(changelog) == ExperimentChangeLog and (
        (
            changelog.old_status == Experiment.STATUS_ACCEPTED
            and changelog.new_status == Experiment.STATUS_ACCEPTED
        )
        or (
            changelog.old_status == Experiment.STATUS_LIVE
            and changelog.new_status == Experiment.STATUS_LIVE
        )
    )


def get_event_reason(changelog, event):
    if event == ReportLog.Event.CREATE:
        return get_create_event_reason(changelog)
    elif event == ReportLog.Event.UPDATE:
        return get_update_event_reason(changelog)
    return get_end_event_reason(changelog)


def get_create_event_reason(changelog):
    if changelog.message:
        if "Cloned" in changelog.message:
            return ReportLog.EventReason.CLONE
        elif "Relaunch" in changelog.message:
            return ReportLog.EventReason.RELAUNCH
    return ReportLog.EventReason.NEW


def is_in_qa_testing(changelog):
    return (
        changelog.old_status == ReportLog.ExperimentStatus.DRAFT
        and changelog.new_status == ReportLog.ExperimentStatus.PREVIEW
    ) or (
        changelog.old_status == ReportLog.ExperimentStatus.ACCEPTED
        and changelog.new_status == ReportLog.ExperimentStatus.ACCEPTED
    )


def is_launch(changelog):
    return (
        changelog.old_status == ReportLog.ExperimentStatus.DRAFT
        or changelog.old_status == ReportLog.ExperimentStatus.ACCEPTED
    ) and changelog.new_status == ReportLog.ExperimentStatus.LIVE


def is_status_change(changelog):
    return changelog.old_status != changelog.new_status


def is_recipe_change(changelog):
    return (
        type(changelog) == ExperimentChangeLog
        and changelog.old_status == ReportLog.ExperimentStatus.LIVE
        and changelog.new_status == ReportLog.ExperimentStatus.LIVE
    )


def is_enrollment_pause(changelog):
    return changelog.message == "Enrollment Complete"


def get_update_event_reason(changelog):
    if is_launch(changelog):
        return ReportLog.EventReason.LAUNCH
    elif is_status_change(changelog):
        return ReportLog.EventReason.STATUS_CHANGE
    elif is_in_qa_testing(changelog):
        return ReportLog.EventReason.QA_LAUNCH
    elif is_enrollment_pause(changelog):
        return ReportLog.EventReason.PAUSE
    elif is_recipe_change(changelog):
        return ReportLog.EventReason.RECIPE_CHANGE


def get_end_event_reason(changelog):
    if type(changelog) == ExperimentChangeLog and changelog.message:
        return changelog.message
    return ReportLog.EventReason.EXPERIMENT_COMPLETE
