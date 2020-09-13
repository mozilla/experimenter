from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator
from django.db import models

from experimenter.experiments.constants import ExperimentConstants
from experimenter.projects.models import Project


class NimbusExperiment(ExperimentConstants, models.Model):
    owner = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="owned_nimbusexperiments",
    )
    status = models.CharField(
        max_length=255,
        default=ExperimentConstants.STATUS_DRAFT,
        choices=ExperimentConstants.STATUS_CHOICES,
    )
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=255, unique=True, blank=False, null=False)
    public_description = models.TextField(blank=True, null=True)
    is_paused = models.BooleanField(default=False)
    proposed_duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(ExperimentConstants.MAX_DURATION)],
    )
    proposed_enrollment = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(ExperimentConstants.MAX_DURATION)],
    )
    firefox_min_version = models.CharField(
        max_length=255,
        choices=ExperimentConstants.VERSION_CHOICES,
        blank=True,
        null=True,
    )
    firefox_max_version = models.CharField(
        max_length=255,
        choices=ExperimentConstants.VERSION_CHOICES,
        blank=True,
        null=True,
    )
    firefox_channel = models.CharField(
        max_length=255,
        choices=ExperimentConstants.CHANNEL_CHOICES,
        blank=True,
        null=True,
    )
    projects = models.ManyToManyField(Project, blank=True)
    objectives = models.TextField(
        default=ExperimentConstants.OBJECTIVES_DEFAULT, blank=True, null=True
    )
    bugzilla_id = models.CharField(max_length=255, blank=True, null=True)

    features = ArrayField(
        models.CharField(
            max_length=255,
            blank=True,
            null=True,
            choices=ExperimentConstants.RAPID_FEATURE_CHOICES,
        ),
        default=list,
    )
    audience = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=ExperimentConstants.RAPID_AUDIENCE_CHOICES,
    )

    class Meta:
        verbose_name = "NimbusExperiment"
        verbose_name_plural = "NimbusExperiments"

    def __str__(self):
        return self.name
