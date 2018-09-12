from collections import defaultdict
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
            super()
            .get_queryset()
            .prefetch_related(
                "changes",
                "changes__changed_by",
                "owner",
                "comments",
                "comments__created_by",
            )
            .annotate(latest_change=Max("changes__changed_on"))
        )


class Experiment(ExperimentConstants, models.Model):
    type = models.CharField(
        max_length=255,
        default=ExperimentConstants.TYPE_PREF,
        choices=ExperimentConstants.TYPE_CHOICES,
    )
    owner = models.ForeignKey(get_user_model(), blank=True, null=True)
    project = models.ForeignKey(
        "projects.Project", blank=True, null=True, related_name="experiments"
    )
    status = models.CharField(
        max_length=255,
        default=ExperimentConstants.STATUS_DRAFT,
        choices=ExperimentConstants.STATUS_CHOICES,
    )
    archived = models.BooleanField(default=False)
    name = models.CharField(
        max_length=255, unique=True, blank=False, null=False
    )
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False
    )
    short_description = models.TextField(default="", blank=True, null=True)
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
        max_digits=7, decimal_places=4, default="0"
    )
    firefox_version = models.CharField(
        max_length=255, choices=ExperimentConstants.VERSION_CHOICES
    )
    firefox_channel = models.CharField(
        max_length=255, choices=ExperimentConstants.CHANNEL_CHOICES
    )
    client_matching = models.TextField(
        default=ExperimentConstants.CLIENT_MATCHING_DEFAULT, blank=True
    )
    objectives = models.TextField(
        default=ExperimentConstants.OBJECTIVES_DEFAULT, blank=True, null=True
    )
    analysis = models.TextField(
        default=ExperimentConstants.ANALYSIS_DEFAULT, blank=True, null=True
    )
    analysis_owner = models.CharField(max_length=255, blank=True, null=True)

    testing = models.TextField(
        default=ExperimentConstants.TESTING_DEFAULT, blank=True, null=True
    )
    total_users = models.PositiveIntegerField(default=0)
    enrollment_dashboard_url = models.URLField(blank=True, null=True)
    dashboard_url = models.URLField(blank=True, null=True)
    dashboard_image_url = models.URLField(blank=True, null=True)
    bugzilla_id = models.CharField(max_length=255, blank=True, null=True)

    # Risk fields
    risk_partner_related = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_brand = models.NullBooleanField(default=None, blank=True, null=True)
    risk_fast_shipped = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_confidential = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_release_population = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risks = models.TextField(
        default=ExperimentConstants.RISKS_DEFAULT, blank=True, null=True
    )

    # Review Fields
    review_phd = models.NullBooleanField(default=None, blank=True, null=True)
    review_science = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_peer = models.NullBooleanField(default=None, blank=True, null=True)
    review_relman = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_qa = models.NullBooleanField(default=None, blank=True, null=True)
    review_legal = models.NullBooleanField(default=None, blank=True, null=True)
    review_ux = models.NullBooleanField(default=None, blank=True, null=True)
    review_security = models.NullBooleanField(
        default=None, blank=True, null=True
    )

    objects = ExperimentManager()

    def __str__(self):  # pragma: no cover
        return "{type}: {name}".format(
            type=self.get_type_display(), name=self.name
        )

    class Meta:
        verbose_name = "Experiment"
        verbose_name_plural = "Experiments"

    @models.permalink
    def get_absolute_url(self):
        return ("experiments-detail", (), {"slug": self.slug})

    @property
    def experiment_url(self):
        return urljoin(
            "https://{host}".format(host=settings.HOSTNAME),
            self.get_absolute_url(),
        )

    @property
    def accept_url(self):
        return urljoin(
            "https://{host}".format(host=settings.HOSTNAME),
            reverse("experiments-api-accept", kwargs={"slug": self.slug}),
        )

    @property
    def reject_url(self):
        return urljoin(
            "https://{host}".format(host=settings.HOSTNAME),
            reverse("experiments-api-reject", kwargs={"slug": self.slug}),
        )

    @property
    def bugzilla_url(self):
        if self.bugzilla_id:
            return settings.BUGZILLA_DETAIL_URL.format(id=self.bugzilla_id)

    @property
    def test_tube_url(self):
        if self.is_begun and self.is_pref_study:
            return (
                "https://firefox-test-tube.herokuapp.com/experiments/{slug}/"
            ).format(slug=self.slug)

    @property
    def has_external_urls(self):
        return self.bugzilla_url or self.test_tube_url

    def _transition_date(self, old_status, new_status):
        for change in self.changes.all():
            if (
                change.old_status == old_status
                and change.new_status == new_status
            ):
                return change.changed_on.date()

    @property
    def start_date(self):
        return (
            self._transition_date(self.STATUS_ACCEPTED, self.STATUS_LIVE)
            or self.proposed_start_date
        )

    @property
    def end_date(self):
        return (
            self._transition_date(self.STATUS_LIVE, self.STATUS_COMPLETE)
            or self.proposed_end_date
        )

    @property
    def duration(self):
        if self.proposed_end_date and self.proposed_start_date:
            return (self.proposed_end_date - self.proposed_start_date).days

    @property
    def dates(self):
        return "{start} - {end} ({duration} days)".format(
            start=self.start_date.strftime("%b %d, %Y")
            if self.start_date
            else "Unknown",
            end=self.end_date.strftime("%b %d, %Y")
            if self.end_date
            else "Unknown",
            duration=self.duration,
        )

    @cached_property
    def control(self):
        return self.variants.get(is_control=True)

    @property
    def grouped_changes(self):
        grouped_changes = defaultdict(lambda: defaultdict(set))

        for change in self.changes.all():
            grouped_changes[change.changed_on.date()][change.changed_by].add(
                change
            )

        return grouped_changes

    @property
    def ordered_changes(self):
        date_ordered_changes = []
        for date, users in sorted(self.grouped_changes.items(), reverse=True):

            date_changes = []
            for user, user_changes in users.items():
                date_changes.append(
                    (user, set([str(c) for c in list(user_changes)]))
                )

            date_ordered_changes.append((date, date_changes))

        return date_ordered_changes

    @property
    def is_addon_study(self):
        return self.type == self.TYPE_ADDON

    @property
    def is_pref_study(self):
        return self.type == self.TYPE_PREF

    @property
    def is_editable(self):
        return self.status in (self.STATUS_DRAFT, self.STATUS_REVIEW)

    @property
    def is_begun(self):
        return self.status in (self.STATUS_LIVE, self.STATUS_COMPLETE)

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
            self.objectives != self.OBJECTIVES_DEFAULT
            and self.analysis != self.ANALYSIS_DEFAULT
        )

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
    def completed_risks(self):
        return (
            None not in self._risk_questions
            and self.testing != self.TESTING_DEFAULT
        )

    @property
    def _required_reviews(self):
        return (
            self.review_phd,
            self.review_science,
            self.review_peer,
            self.review_relman,
            self.review_qa,
        )

    @property
    def completed_required_reviews(self):
        return all(self._required_reviews)

    @property
    def completed_all_sections(self):
        return (
            self.completed_overview
            and self.completed_variants
            and self.completed_objectives
            and self.completed_risks
        )

    @property
    def is_ready_to_launch(self):
        return self.completed_all_sections and self.completed_required_reviews

    @property
    def population(self):
        return "{percent:g}% of {channel} Firefox {version}".format(
            percent=float(self.population_percent),
            version=self.firefox_version,
            channel=self.firefox_channel,
        )


class ExperimentVariant(models.Model):
    experiment = models.ForeignKey(
        Experiment, blank=False, null=False, related_name="variants"
    )
    name = models.CharField(max_length=255, blank=False, null=False)
    slug = models.SlugField(max_length=255, blank=False, null=False)
    is_control = models.BooleanField(default=False)
    description = models.TextField(default="")
    ratio = models.PositiveIntegerField(default=1)
    value = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Experiment Variant"
        verbose_name_plural = "Experiment Variants"
        unique_together = (("slug", "experiment"),)

    def __str__(self):  # pragma: no cover
        return self.name

    @property
    def type(self):
        if self.is_control:
            return "Control"
        else:
            return "Treatment"


class ExperimentChangeLogManager(models.Manager):

    def latest(self):
        return self.all().order_by("-changed_on").first()


class ExperimentChangeLog(models.Model):
    STATUS_NONE_DRAFT = "Created Draft"
    STATUS_DRAFT_DRAFT = "Edited Draft"
    STATUS_DRAFT_REVIEW = "Submitted Draft for Review"
    STATUS_REVIEW_DRAFT = "Cancelled Review Request"
    STATUS_REVIEW_SHIP = "Marked as Ready to Ship"
    STATUS_REVIEW_REJECTED = "Review Rejected"
    STATUS_SHIP_ACCEPTED = "Accepted by Shield"
    STATUS_SHIP_REVIEW = "Canceled Ready to Ship"
    STATUS_ACCEPTED_LIVE = "Launched Experiment"
    STATUS_LIVE_COMPLETE = "Completed Experiment"
    STATUS_REJECTED = "Rejected Experiment"

    PRETTY_STATUS_LABELS = {
        None: {Experiment.STATUS_DRAFT: STATUS_NONE_DRAFT},
        Experiment.STATUS_DRAFT: {
            Experiment.STATUS_DRAFT: STATUS_DRAFT_DRAFT,
            Experiment.STATUS_REVIEW: STATUS_DRAFT_REVIEW,
        },
        Experiment.STATUS_REVIEW: {
            Experiment.STATUS_DRAFT: STATUS_REVIEW_DRAFT,
            Experiment.STATUS_SHIP: STATUS_REVIEW_SHIP,
            Experiment.STATUS_REJECTED: STATUS_REVIEW_REJECTED,
        },
        Experiment.STATUS_SHIP: {
            Experiment.STATUS_REVIEW: STATUS_SHIP_REVIEW,
            Experiment.STATUS_ACCEPTED: STATUS_SHIP_ACCEPTED,
        },
        Experiment.STATUS_ACCEPTED: {
            Experiment.STATUS_LIVE: STATUS_ACCEPTED_LIVE
        },
        Experiment.STATUS_LIVE: {
            Experiment.STATUS_COMPLETE: STATUS_LIVE_COMPLETE
        },
    }

    def current_datetime():
        return timezone.now()

    experiment = models.ForeignKey(
        Experiment, blank=False, null=False, related_name="changes"
    )
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
        verbose_name = "Experiment Change Log"
        verbose_name_plural = "Experiment Change Logs"
        ordering = ("changed_on",)

    def __str__(self):  # pragma: no cover
        if self.message:
            return self.message
        else:
            return self.pretty_status

    @property
    def pretty_status(self):
        return self.PRETTY_STATUS_LABELS.get(self.old_status, {}).get(
            self.new_status, ""
        )


class ExperimentCommentManager(models.Manager):

    @cached_property
    def sections(self):
        sections = defaultdict(list)

        for comment in self.all():
            sections[comment.section].append(comment)

        return sections


class ExperimentComment(ExperimentConstants, models.Model):
    experiment = models.ForeignKey(Experiment, related_name="comments")
    created_by = models.ForeignKey(get_user_model())
    created_on = models.DateTimeField(auto_now_add=True)
    section = models.CharField(
        max_length=255, choices=ExperimentConstants.SECTION_CHOICES
    )
    text = models.TextField()

    objects = ExperimentCommentManager()

    class Meta:
        verbose_name = "Experiment Comment"
        verbose_name_plural = "Experiment Comments"
        ordering = ("created_on",)

    def __str__(self):  # pragma: no cover
        return "{author} ({date}): {text}".format(
            author=self.created_by, date=self.created_on, text=self.text
        )
