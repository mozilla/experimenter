import datetime

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models


class ExperimentManager(models.Manager):

    def started(self):
        return self.get_queryset().filter(status=Experiment.EXPERIMENT_STARTED)


class Experiment(models.Model):
    EXPERIMENT_NOT_STARTED = 'Not Started'
    EXPERIMENT_STARTED = 'Started'
    EXPERIMENT_COMPLETE = 'Complete'

    EXPERIMENT_STATUS_CHOICES = (
        (EXPERIMENT_NOT_STARTED, EXPERIMENT_NOT_STARTED),
        (EXPERIMENT_STARTED, EXPERIMENT_STARTED),
        (EXPERIMENT_COMPLETE, EXPERIMENT_COMPLETE),
    )

    status = models.CharField(
        max_length=255,
        default=EXPERIMENT_NOT_STARTED,
        choices=EXPERIMENT_STATUS_CHOICES,
    )
    project = models.ForeignKey('projects.Project', blank=False, null=False)
    name = models.CharField(
        max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False)
    objectives = models.TextField(default='')
    success_criteria = models.TextField(default='')
    analysis = models.TextField(default='')
    created_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    objects = ExperimentManager()

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = 'Experiment'
        verbose_name_plural = 'Experiments'

    def clean(self):
        if not self.pk:
            return

        old_state = Experiment.objects.get(pk=self.pk)
        new_state = self

        if old_state.status != new_state.status:
            if (
                old_state.status == self.EXPERIMENT_NOT_STARTED and
                new_state.status == self.EXPERIMENT_STARTED
            ):
                self.start_date = datetime.datetime.now()

            elif (
                old_state.status == self.EXPERIMENT_STARTED and
                new_state.status == self.EXPERIMENT_COMPLETE
            ):
                self.end_date = datetime.datetime.now()

            else:
                raise ValidationError((
                    'You can not change an Experiment\'s status '
                    'from {old_status} to {new_status}'
                ).format(
                    old_status=old_state.status, new_status=new_state.status))

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def is_begun(self):
        return self.status != self.EXPERIMENT_NOT_STARTED

    @property
    def is_complete(self):
        return self.status == self.EXPERIMENT_COMPLETE

    @property
    def control(self):
        return self.variants.get(is_control=True)

    @property
    def variant(self):
        return self.variants.get(is_control=False)


class ExperimentVariant(models.Model):
    experiment = models.ForeignKey(
        Experiment, blank=False, null=False, related_name='variants')
    name = models.CharField(
        max_length=255, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, blank=False, null=False)
    is_control = models.BooleanField(default=False)
    description = models.TextField(default='')
    threshold = models.DecimalField(
        max_digits=6, decimal_places=4, default='0')
    value = JSONField(default=False)

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = 'Experiment Variant'
        verbose_name_plural = 'Experiment Variants'
        unique_together = (
            ('slug', 'experiment'),
            ('is_control', 'experiment'),
        )

    @property
    def experiment_variant_slug(self):
        return '{experiment_slug}:{variant_slug}'.format(
            experiment_slug=self.experiment.slug,
            variant_slug=self.slug,
        )
