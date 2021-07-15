from django.db import models


class Event(models.TextChoices):
    CREATE = "Create"
    UPDATE = "Update"
    END = "End"


class EventReason(models.TextChoices):
    NEW = "New"
    CLONE = "Clone"
    RELAUNCH = "Relaunch"
    STATUS_CHANGE = "Status Change"
    PAUSE = "Pause"
    RECIPE_CHANGE = "Recipe Change"
    QA_LAUNCH = "QA Launch"
    LAUNCH = "Launch"
    EXPERIMENT_COMPLETE = "Experiment Complete"
    FILTERING_ISSUE = "Filtering Issue"
    ENROLLMENT_ISSUE = "Enrollment Issue"
    EXPERIMENT_DESIGN_ISSUE = "Experiment Design Issue"
    RESULTS_ADDED = "Results Added"


class ReportLogConstants(object):
    class ExperimentStatus(models.TextChoices):
        DRAFT = "Draft"
        PREVIEW = "Preview"
        REVIEW = "Review"
        SHIP = "Ship"
        ACCEPTED = "Accepted"
        LIVE = "Live"
        COMPLETE = "Complete"

    class ExperimentType(models.TextChoices):
        NORMANDY_PREF = "Normandy-Pref"
        NORMANDY_ADDON = "Normandy-Addon"
        NORMANDY_ROLLOUT = "Normandy-Rollout"
        NIMBUS_DESKTOP = "Nimbus-Firefox-Desktop"
        NIMBUS_FENIX = "Nimbus-Fenix"
        NIMBUS_IOS = "Nimbus-Ios"

    Event = Event
    EventReason = EventReason

    EVENT_PAIRS = {
        Event.CREATE: [EventReason.NEW, EventReason.CLONE],
        Event.UPDATE: [
            EventReason.STATUS_CHANGE,
            EventReason.PAUSE,
            EventReason.RECIPE_CHANGE,
            EventReason.QA_LAUNCH,
            EventReason.LAUNCH,
            EventReason.RESULTS_ADDED,
        ],
        Event.END: [
            EventReason.EXPERIMENT_COMPLETE,
            EventReason.FILTERING_ISSUE,
            EventReason.ENROLLMENT_ISSUE,
            EventReason.EXPERIMENT_DESIGN_ISSUE,
        ],
    }
