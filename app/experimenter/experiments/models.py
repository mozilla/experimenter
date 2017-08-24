from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models


class Experiment(models.Model):
    STATUS_CREATED = 'Created'
    STATUS_PENDING = 'Pending'
    STATUS_ACCEPTED = 'Accepted'
    STATUS_LAUNCHED = 'Launched'
    STATUS_COMPLETE = 'Complete'
    STATUS_REJECTED = 'Rejected'

    STATUS_CHOICES = (
        (STATUS_CREATED, STATUS_CREATED),
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_ACCEPTED, STATUS_ACCEPTED),
        (STATUS_LAUNCHED, STATUS_LAUNCHED),
        (STATUS_COMPLETE, STATUS_COMPLETE),
        (STATUS_REJECTED, STATUS_REJECTED),
    )

    STATUS_TRANSITIONS = {
        STATUS_CREATED: [
            STATUS_PENDING,
            STATUS_REJECTED,
        ],
        STATUS_PENDING: [
            STATUS_ACCEPTED,
            STATUS_REJECTED,
        ],
        STATUS_ACCEPTED: [
            STATUS_LAUNCHED,
            STATUS_REJECTED,
        ],
        STATUS_LAUNCHED: [
            STATUS_COMPLETE,
        ],
        STATUS_COMPLETE: [
        ],
        STATUS_REJECTED: [
        ],
    }

    CHANNEL_NIGHTLY = 'Nightly'
    CHANNEL_BETA = 'Beta'
    CHANNEL_RELEASE = 'Release'

    CHANNEL_CHOICES = (
        (CHANNEL_NIGHTLY, CHANNEL_NIGHTLY),
        (CHANNEL_BETA, CHANNEL_BETA),
        (CHANNEL_RELEASE, CHANNEL_RELEASE),
    )

    PREF_TYPE_BOOL = 'bool'
    PREF_TYPE_INT = 'int'
    PREF_TYPE_STR = 'str'

    PREF_TYPE_CHOICES = (
        (PREF_TYPE_BOOL, PREF_TYPE_BOOL),
        (PREF_TYPE_INT, PREF_TYPE_INT),
        (PREF_TYPE_STR, PREF_TYPE_STR),
    )

    status = models.CharField(
        max_length=255,
        default=STATUS_CREATED,
        choices=STATUS_CHOICES,
    )
    project = models.ForeignKey(
        'projects.Project',
        blank=False,
        null=False,
        related_name='experiments',
    )
    pref_key = models.CharField(max_length=255, blank=True, null=True)
    pref_type = models.CharField(
        max_length=255,
        choices=PREF_TYPE_CHOICES,
        default=PREF_TYPE_BOOL,
    )
    firefox_version = models.CharField(max_length=255)
    firefox_channel = models.CharField(
        max_length=255, choices=CHANNEL_CHOICES, default=CHANNEL_NIGHTLY)
    name = models.CharField(
        max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False)
    objectives = models.TextField(default='')
    analysis = models.TextField(default='')
    created_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    dashboard_url = models.URLField(blank=True, null=True)
    dashboard_image_url = models.URLField(blank=True, null=True)
    population_percent = models.DecimalField(
        max_digits=6, decimal_places=4, default='0')

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = 'Experiment'
        verbose_name_plural = 'Experiments'

    def clean_status(self):
        if not self.pk:
            return

        old_status = Experiment.objects.get(pk=self.pk).status
        new_status = self.status
        expected_new_status = new_status in self.STATUS_TRANSITIONS[old_status]

        if old_status != new_status and not expected_new_status:
            raise ValidationError({'status': (
                'You can not change an Experiment\'s status '
                'from {old_status} to {new_status}'
            ).format(
                old_status=old_status, new_status=new_status)})

    def clean(self):
        self.clean_status()

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def control(self):
        return self.variants.get(is_control=True)

    @property
    def variant(self):
        return self.variants.get(is_control=False)

    @property
    def is_readonly(self):
        return self.status != self.STATUS_CREATED


class ExperimentVariant(models.Model):
    experiment = models.ForeignKey(
        Experiment, blank=False, null=False, related_name='variants')
    name = models.CharField(
        max_length=255, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, blank=False, null=False)
    is_control = models.BooleanField(default=False)
    description = models.TextField(default='')
    ratio = models.PositiveIntegerField(default=1)
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


class ExperimentChangeLog(models.Model):
    experiment = models.ForeignKey(
        Experiment, blank=False, null=False, related_name='changes')
    changed_on = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(get_user_model())
    old_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=Experiment.STATUS_CHOICES,
    )
    new_status = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        choices=Experiment.STATUS_CHOICES,
    )
    message = models.TextField()

    def __str__(self):  # pragma: no cover
        return (
            '{changed_by} changed {experiment} on {datetime}: {message}'
        ).format(
            changed_by=self.changed_by,
            experiment=self.experiment,
            datetime=self.changed_on,
            message=self.message,
        )

    class Meta:
        verbose_name = 'Experiment Change Log'
        verbose_name_plural = 'Experiment Change Logs'
