from django.contrib.postgres.fields import JSONField
from django.db import models


class Experiment(models.Model):
    active = models.BooleanField(default=False)
    project = models.ForeignKey('projects.Project', blank=False, null=False)
    name = models.CharField(
        max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False)
    objectives = models.TextField(default='')
    success_criteria = models.TextField(default='')
    analysis = models.TextField(default='')
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = 'Experiment'
        verbose_name_plural = 'Experiments'


class ExperimentVariant(models.Model):
    experiment = models.ForeignKey(Experiment, blank=False, null=False)
    name = models.CharField(
        max_length=255, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, blank=False, null=False)
    is_control = models.BooleanField(default=False)
    description = models.TextField(default='')
    threshold = models.PositiveIntegerField(default=0)
    value = JSONField(default=False)

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = 'Experiment Variant'
        verbose_name_plural = 'Experiment Variants'
        unique_together = ('slug', 'experiment')
