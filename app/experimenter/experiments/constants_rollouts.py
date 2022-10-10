from dataclasses import dataclass
from typing import Dict

from django.conf import settings
from django.db import models
from packaging import version

class NimbusRolloutConstants(object):
    class Status(models.TextChoices):
        DRAFT = "Draft"
        PREVIEW = "Preview"
        PUBLISHED = "Published"
        UNPUBLISHED = "Unpublished"

    class PublishStatus(models.TextChoices):
        IDLE = "Idle"
        REVIEW = "Review"
        APPROVED = "Approved"
        WAITING = "Waiting"
    
    class DataStatus(models.TextChoices):
        CLEAN = "Clean"
        DIRTY = "Dirty"
    
    class Type(models.TextChoices):
        EXPERIMENT = "Experiment"
        ROLLOUT = "Rollout"

    VALID_STATUS_TRANSITIONS = {
        Status.DRAFT: (Status.PREVIEW,),
        Status.PREVIEW: (Status.DRAFT,),
    }
    STATUS_ALLOWS_UPDATE = (
        Status.DRAFT, 
        Status.PUBLISHED, # we're allowed to make edits from a published state
        Status.UNPUBLISHED,
    )

    PUBLISH_STATUS_ALLOWS_UPDATE = (
        PublishStatus.IDLE, 
        PublishStatus.APPROVED, # regular experiments only have idle, should this also be APPROVED?
    )

    # Valid status_next values for given status values
    VALID_STATUS_NEXT_VALUES = {
        Status.DRAFT: (None, Status.PUBLISHED),
        Status.PREVIEW: (None, Status.PUBLISHED), # does preview have to go back to draft?
        Status.PUBLISHED: (None, Status.PUBLISHED, Status.UNPUBLISHED), 
        Status.UNPUBLISHED: (None, Status.PUBLISHED, Status.UNPUBLISHED)
    }

    VALID_PUBLISH_STATUS_TRANSITIONS = { # do our publish statuses change? the review process should be the same
        PublishStatus.IDLE: (PublishStatus.REVIEW, PublishStatus.APPROVED),
        PublishStatus.REVIEW: (PublishStatus.IDLE, PublishStatus.APPROVED),
    }
    
    VALID_DATA_STATUS_TRANSITIONS = {
        DataStatus.CLEAN: (DataStatus.CLEAN, DataStatus.DIRTY),
        DataStatus.DIRTY: (DataStatus.CLEAN, DataStatus.DIRTY),
    }