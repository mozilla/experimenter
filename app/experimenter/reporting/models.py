from django.core.exceptions import ValidationError
from django.db import models

from experimenter.projects.models import Project
from experimenter.reporting.constants import ReportLogConstants


class ReportLog(ReportLogConstants, models.Model):
    timestamp = models.DateTimeField()
    experiment_slug = models.CharField(max_length=255, blank=False, null=False)
    experiment_name = models.CharField(max_length=255, blank=False, null=False)
    experiment_type = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        choices=ReportLogConstants.ExperimentType.choices,
    )
    experiment_old_status = models.CharField(
        max_length=255,
        choices=ReportLogConstants.ExperimentStatus.choices,
        blank=True,
        null=True,
    )
    experiment_new_status = models.CharField(
        max_length=255, choices=ReportLogConstants.ExperimentStatus.choices
    )
    event = models.CharField(max_length=255, choices=ReportLogConstants.Event.choices)
    event_reason = models.CharField(
        max_length=255, choices=ReportLogConstants.EventReason.choices
    )
    comment = models.CharField(max_length=255, blank=True)
    projects = models.ManyToManyField(Project, blank=True)

    def clean(self):
        if self.event_reason not in ReportLogConstants.EVENT_PAIRS[self.event]:
            raise ValidationError(
                "{event_reason} cannot be paired with {event}".format(
                    event_reason=self.event_reason, event=self.event
                )
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.timestamp} - {self.experiment_type} - {self.event_reason} "

    class Meta:
        ordering = ("timestamp",)
        verbose_name = "ReportLog"
        verbose_name_plural = "ReportLogs"
