import datetime
from collections import defaultdict
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Max
from django.urls import reverse
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
    owner = models.ForeignKey(
        get_user_model(), blank=True, null=True, on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        "projects.Project",
        blank=True,
        null=True,
        related_name="experiments",
        on_delete=models.CASCADE,
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
    related_work = models.TextField(default="", blank=True, null=True)

    proposed_start_date = models.DateField(blank=True, null=True)
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
    firefox_min_version = models.CharField(
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

    total_users = models.PositiveIntegerField(default=0)
    enrollment_dashboard_url = models.URLField(blank=True, null=True)
    dashboard_url = models.URLField(blank=True, null=True)
    dashboard_image_url = models.URLField(blank=True, null=True)

    bugzilla_id = models.CharField(max_length=255, blank=True, null=True)

    data_science_bugzilla_url = models.URLField(blank=True, null=True)
    feature_bugzilla_url = models.URLField(blank=True, null=True)

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
    risk_technical = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_technical_description = models.TextField(blank=True, null=True)

    risks = models.TextField(blank=True, null=True)

    # Testing
    testing = models.TextField(blank=True, null=True)
    test_builds = models.TextField(blank=True, null=True)
    qa_status = models.TextField(blank=True, null=True)

    # Review Fields (sign-offs)
    # Required
    review_science = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_engineering = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_qa_requested = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_intent_to_ship = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_bugzilla = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_qa = models.NullBooleanField(default=None, blank=True, null=True)
    review_relman = models.NullBooleanField(
        default=None, blank=True, null=True
    )

    # Optional
    review_advisory = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_legal = models.NullBooleanField(default=None, blank=True, null=True)
    review_ux = models.NullBooleanField(default=None, blank=True, null=True)
    review_security = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_vp = models.NullBooleanField(default=None, blank=True, null=True)
    review_data_steward = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_comms = models.NullBooleanField(default=None, blank=True, null=True)
    review_impacted_teams = models.NullBooleanField(
        default=None, blank=True, null=True
    )

    objects = ExperimentManager()

    class Meta:
        verbose_name = "Experiment"
        verbose_name_plural = "Experiments"

    def get_absolute_url(self):
        return reverse("experiments-detail", kwargs={"slug": self.slug})

    def __str__(self):  # pragma: no cover
        return self.full_name

    @property
    def full_name(self):
        return "{type}: {name}".format(
            type=self.get_type_display(), name=self.name
        )

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
        return (
            self.bugzilla_url
            or self.test_tube_url
            or self.data_science_bugzilla_url
            or self.feature_bugzilla_url
        )

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

    def _compute_end_date(self, duration):
        if self.start_date and duration and 0 <= duration <= self.MAX_DURATION:
            return self.start_date + datetime.timedelta(days=duration)

    @property
    def end_date(self):
        return self._compute_end_date(self.proposed_duration)

    @property
    def enrollment_end_date(self):
        return self._compute_end_date(self.proposed_enrollment)

    @property
    def observation_duration(self):
        if self.proposed_enrollment:
            return self.proposed_duration - self.proposed_enrollment
        return 0

    def _format_date_string(self, start_date, end_date):
        start_text = "Unknown"
        if start_date:
            start_text = start_date.strftime("%b %d, %Y")

        end_text = "Unknown"
        if end_date:
            end_text = end_date.strftime("%b %d, %Y")

        day_text = "days"
        duration_text = "Unknown"
        if start_date and end_date:
            duration = (end_date - start_date).days
            duration_text = str(duration)

            if duration == 1:
                day_text = "day"

        return "{start} - {end} ({duration} {days})".format(
            start=start_text,
            end=end_text,
            duration=duration_text,
            days=day_text,
        )

    @property
    def dates(self):
        return self._format_date_string(self.start_date, self.end_date)

    @property
    def enrollment_dates(self):
        return self._format_date_string(
            self.start_date, self.enrollment_end_date
        )

    @property
    def observation_dates(self):
        return self._format_date_string(
            self.enrollment_end_date, self.end_date
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
        return any(self._risk_questions)

    @property
    def completed_overview(self):
        return self.pk is not None

    @property
    def completed_population(self):
        return (
            self.population_percent > 0
            and self.firefox_min_version != ""
            and self.firefox_channel != ""
        )

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
            self.risk_technical,
        )

    @property
    def completed_risks(self):
        return None not in self._risk_questions

    @property
    def completed_testing(self):
        return self.qa_status

    @property
    def _required_reviews(self):
        return (
            self.review_science,
            self.review_engineering,
            self.review_qa_requested,
            self.review_intent_to_ship,
            self.review_bugzilla,
            self.review_qa,
            self.review_relman,
        )

    @property
    def completed_required_reviews(self):
        return all(self._required_reviews)

    @property
    def completed_all_sections(self):
        return (
            self.completed_population
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
            version=self.firefox_min_version,
            channel=self.firefox_channel,
        )


class ExperimentVariant(models.Model):
    experiment = models.ForeignKey(
        Experiment,
        blank=False,
        null=False,
        related_name="variants",
        on_delete=models.CASCADE,
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
    STATUS_DRAFT_REVIEW = "Ready for Sign-Off"
    STATUS_REVIEW_DRAFT = "Return to Draft"
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
        Experiment,
        blank=False,
        null=False,
        related_name="changes",
        on_delete=models.CASCADE,
    )
    changed_on = models.DateTimeField(default=current_datetime)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
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
    experiment = models.ForeignKey(
        Experiment, related_name="comments", on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
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
