from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max
from django.utils import timezone


class ExperimentManager(models.Manager):

    def most_recently_changed(self):
        return (
            self.all()
            .annotate(latest_change=Max('changes__changed_on'))
            .order_by('-latest_change')
        )


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

    PREF_TYPE_BOOL = 'boolean'
    PREF_TYPE_INT = 'integer'
    PREF_TYPE_STR = 'string'

    PREF_TYPE_CHOICES = (
        (PREF_TYPE_BOOL, PREF_TYPE_BOOL),
        (PREF_TYPE_INT, PREF_TYPE_INT),
        (PREF_TYPE_STR, PREF_TYPE_STR),
    )

    PREF_BRANCH_USER = 'user'
    PREF_BRANCH_DEFAULT = 'default'
    PREF_BRANCH_CHOICES = (
        (PREF_BRANCH_DEFAULT, PREF_BRANCH_DEFAULT),
        (PREF_BRANCH_USER, PREF_BRANCH_USER),
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
    )
    pref_branch = models.CharField(
        max_length=255,
        choices=PREF_BRANCH_CHOICES,
        default=PREF_BRANCH_DEFAULT,
    )
    firefox_version = models.CharField(max_length=255)
    firefox_channel = models.CharField(
        max_length=255, choices=CHANNEL_CHOICES, default=CHANNEL_NIGHTLY)
    client_matching = models.TextField(default='', blank=True)
    name = models.CharField(
        max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False)
    objectives = models.TextField(default='')
    analysis = models.TextField(default='', blank=True, null=True)
    dashboard_url = models.URLField(blank=True, null=True)
    dashboard_image_url = models.URLField(blank=True, null=True)
    population_percent = models.DecimalField(
        max_digits=7, decimal_places=4, default='0')

    objects = ExperimentManager()

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

    def clean(self, validate=False):
        if validate:
            self.clean_status()

    def save(self, validate=False, *args, **kwargs):
        self.clean(validate=validate)
        return super().save(*args, **kwargs)

    @property
    def control(self):
        return self.variants.filter(is_control=True).first()

    @property
    def variant(self):
        return self.variants.filter(is_control=False).first()

    @property
    def is_readonly(self):
        return self.status != self.STATUS_CREATED

    def _transition_date(self, start_state, end_state):
        change = self.changes.filter(
            old_status=start_state,
            new_status=end_state,
        )

        if change.count() == 1:
            return change.get().changed_on

    @property
    def start_date(self):
        return self._transition_date(
            self.STATUS_ACCEPTED,
            self.STATUS_LAUNCHED,
        )

    @property
    def end_date(self):
        return self._transition_date(
            self.STATUS_LAUNCHED,
            self.STATUS_COMPLETE,
        )

    @property
    def experiment_slug(self):
        return 'pref-flip-{project_slug}-{experiment_slug}'.format(
            project_slug=self.project.slug,
            experiment_slug=self.slug,
        )

    @property
    def experiment_url(self):
        return urljoin(
            'https://{host}'.format(host=settings.HOSTNAME),
            reverse('admin:experiments_experiment_change', args=[self.pk])
        )

    @property
    def accept_url(self):
        return urljoin(
            'https://{host}'.format(host=settings.HOSTNAME),
            reverse('experiments-accept', kwargs={'slug': self.slug})
        )

    @property
    def reject_url(self):
        return urljoin(
            'https://{host}'.format(host=settings.HOSTNAME),
            reverse('experiments-reject', kwargs={'slug': self.slug})
        )


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


class ExperimentChangeLogManager(models.Manager):

    def latest(self):
        return self.all().order_by('-changed_on').first()


class ExperimentChangeLog(models.Model):
    def current_datetime():
        return timezone.now()

    experiment = models.ForeignKey(
        Experiment, blank=False, null=False, related_name='changes')
    changed_on = models.DateTimeField(default=current_datetime)
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
    message = models.TextField(blank=True, null=True)

    objects = ExperimentChangeLogManager()

    def __str__(self):  # pragma: no cover
        return '{status} by {updater} on {datetime}'.format(
          status=self.new_status,
          updater=self.changed_by,
          datetime=self.changed_on.date(),
        )

    class Meta:
        verbose_name = 'Experiment Change Log'
        verbose_name_plural = 'Experiment Change Logs'
        ordering = ('changed_on',)
