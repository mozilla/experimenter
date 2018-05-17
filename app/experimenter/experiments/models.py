from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max
from django.utils import timezone
from django.utils.functional import cached_property

from experimenter.experiments.constants import ExperimentConstants


class ExperimentManager(models.Manager):

    def get_queryset(self):
        return (
            super().get_queryset()
            .annotate(latest_change=Max('changes__changed_on'))
        )


class Experiment(ExperimentConstants, models.Model):
    owner = models.ForeignKey(get_user_model(), blank=True, null=True)
    project = models.ForeignKey(
        'projects.Project',
        blank=True,
        null=True,
        related_name='experiments',
    )
    status = models.CharField(
        max_length=255,
        default=ExperimentConstants.STATUS_DRAFT,
        choices=ExperimentConstants.STATUS_CHOICES,
    )
    archived = models.BooleanField(default=False)
    name = models.CharField(
        max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False)
    short_description = models.TextField(default='', blank=True, null=True)
    proposed_start_date = models.DateField(blank=True, null=True)
    proposed_end_date = models.DateField(blank=True, null=True)
    pref_key = models.CharField(max_length=255, blank=True, null=True)
    pref_type = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PREF_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    pref_branch = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PREF_BRANCH_CHOICES,
        blank=True,
        null=True,
    )
    population_percent = models.DecimalField(
        max_digits=7, decimal_places=4, default='0')
    firefox_version = models.CharField(
        max_length=255, choices=ExperimentConstants.VERSION_CHOICES)
    firefox_channel = models.CharField(
        max_length=255, choices=ExperimentConstants.CHANNEL_CHOICES)
    client_matching = models.TextField(default='', blank=True)
    objectives = models.TextField(
        default=ExperimentConstants.OBJECTIVES_DEFAULT, blank=True, null=True)
    analysis = models.TextField(
        default=ExperimentConstants.ANALYSIS_DEFAULT, blank=True, null=True)
    risk_partner_related = models.NullBooleanField(
        default=None, blank=True, null=True)
    risk_brand = models.NullBooleanField(
        default=None, blank=True, null=True)
    risk_fast_shipped = models.NullBooleanField(
        default=None, blank=True, null=True)
    risk_confidential = models.NullBooleanField(
        default=None, blank=True, null=True)
    risk_release_population = models.NullBooleanField(
        default=None, blank=True, null=True)
    risks = models.TextField(
        default=ExperimentConstants.RISKS_DEFAULT, blank=True, null=True)
    testing = models.TextField(
        default=ExperimentConstants.TESTING_DEFAULT, blank=True, null=True)
    total_users = models.PositiveIntegerField(default=0)
    enrollment_dashboard_url = models.URLField(blank=True, null=True)
    dashboard_url = models.URLField(blank=True, null=True)
    dashboard_image_url = models.URLField(blank=True, null=True)

    objects = ExperimentManager()

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = 'Experiment'
        verbose_name_plural = 'Experiments'

    @cached_property
    def control(self):
        return self.variants.filter(is_control=True).first()

    @cached_property
    def variant(self):
        return self.variants.filter(is_control=False).first()

    @property
    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    @property
    def is_in_review(self):
        return self.status == self.STATUS_REVIEW

    @property
    def is_readonly(self):
        return not self.is_draft

    @property
    def is_begun(self):
        return self.status in (self.STATUS_LIVE, self.STATUS_COMPLETE)

    def _transition_date(self, start_state, end_state):
        change = self.changes.filter(
            old_status=start_state,
            new_status=end_state,
        )

        if change.count() == 1:
            return change.get().changed_on

    @property
    def population(self):
        return '{percent:g}% of {channel} Firefox {version}'.format(
            percent=float(self.population_percent),
            version=self.firefox_version,
            channel=self.firefox_channel,
        )

    @property
    def start_date(self):
        return self._transition_date(
            self.STATUS_ACCEPTED,
            self.STATUS_LIVE,
        )

    @property
    def end_date(self):
        return self._transition_date(
            self.STATUS_LIVE,
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
            reverse('experiments-detail', args=[self.slug])
        )

    @property
    def accept_url(self):
        return urljoin(
            'https://{host}'.format(host=settings.HOSTNAME),
            reverse('experiments-api-accept', kwargs={'slug': self.slug})
        )

    @property
    def reject_url(self):
        return urljoin(
            'https://{host}'.format(host=settings.HOSTNAME),
            reverse('experiments-api-reject', kwargs={'slug': self.slug})
        )

    @property
    def test_tube_url(self):
        return (
            'https://firefox-test-tube.herokuapp.com/experiments/{slug}/'
        ).format(slug=self.slug)

    @property
    def _risk_questions(self):
        return (
            self.risk_partner_related,
            self.risk_brand,
            self.risk_fast_shipped,
            self.risk_confidential,
            self.risk_release_population,
        )

    @property
    def is_high_risk(self):
        return True in self._risk_questions

    @property
    def completed_overview(self):
        return self.pk is not None

    @property
    def completed_variants(self):
        return self.variants.exists()

    @property
    def completed_objectives(self):
        return (
            self.objectives != self.OBJECTIVES_DEFAULT and
            self.analysis != self.ANALYSIS_DEFAULT
        )

    @property
    def completed_risks(self):
        return (
            None not in self._risk_questions and
            self.testing != self.TESTING_DEFAULT
        )

    @property
    def is_ready_for_review(self):
        return (
            self.completed_overview and
            self.completed_variants and
            self.completed_objectives and
            self.completed_risks
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
    STATUS_NONE_DRAFT = 'Created Draft'
    STATUS_DRAFT_DRAFT = 'Edited Draft'
    STATUS_DRAFT_REVIEW = 'Submitted for Review'
    STATUS_REVIEW_DRAFT = 'Cancelled Review Request'
    STATUS_REVIEW_ACCEPTED = 'Review Approved'
    STATUS_REVIEW_REJECTED = 'Review Rejected'
    STATUS_ACCEPTED_LIVE = 'Launched'
    STATUS_LIVE_COMPLETE = 'Complete'

    PRETTY_STATUS_LABELS = {
        None: {
            Experiment.STATUS_DRAFT: STATUS_NONE_DRAFT,
        },
        Experiment.STATUS_DRAFT: {
            Experiment.STATUS_DRAFT: STATUS_DRAFT_DRAFT,
            Experiment.STATUS_REVIEW: STATUS_DRAFT_REVIEW,
        },
        Experiment.STATUS_REVIEW: {
            Experiment.STATUS_DRAFT: STATUS_REVIEW_DRAFT,
            Experiment.STATUS_ACCEPTED: STATUS_REVIEW_ACCEPTED,
            Experiment.STATUS_REJECTED: STATUS_REVIEW_REJECTED,
        },
        Experiment.STATUS_ACCEPTED: {
            Experiment.STATUS_LIVE: STATUS_ACCEPTED_LIVE,
        },
        Experiment.STATUS_LIVE: {
            Experiment.STATUS_COMPLETE: STATUS_LIVE_COMPLETE,
        },
    }

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

    class Meta:
        verbose_name = 'Experiment Change Log'
        verbose_name_plural = 'Experiment Change Logs'
        ordering = ('changed_on',)

    def __str__(self):  # pragma: no cover
        return '{status} by {updater} on {datetime}'.format(
          status=self.new_status,
          updater=self.changed_by,
          datetime=self.changed_on.date(),
        )

    @property
    def pretty_status(self):
        return self.PRETTY_STATUS_LABELS.get(
            self.old_status, {}).get(self.new_status, '')
