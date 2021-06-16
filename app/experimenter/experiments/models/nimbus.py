import datetime
import time
from decimal import Decimal
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from experimenter.base.models import Country, Locale
from experimenter.experiments.constants import NimbusConstants
from experimenter.projects.models import Project


class FilterMixin:
    def has_filter(self, filter):
        return type(self).objects.filter(id=self.id).filter(filter).exists()


class NimbusExperimentManager(models.Manager):
    def launch_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_LAUNCH_QUEUED,
            application__in=applications,
        )

    def pause_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_PAUSE_QUEUED,
            application__in=applications,
            id__in=[
                experiment.id for experiment in self.all() if experiment.should_pause
            ],
        )

    def end_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_END_QUEUED,
            application__in=applications,
        )

    def waiting(self, applications):
        return self.filter(
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            application__in=applications,
        )

    def waiting_to_launch_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_LAUNCHING, application__in=applications
        )

    def waiting_to_pause_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_PAUSING, application__in=applications
        )


class NimbusExperiment(NimbusConstants, FilterMixin, models.Model):
    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="owned_nimbusexperiments",
    )
    status = models.CharField(
        max_length=255,
        default=NimbusConstants.Status.DRAFT.value,
        choices=NimbusConstants.Status.choices,
    )
    status_next = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=NimbusConstants.Status.choices,
    )
    publish_status = models.CharField(
        max_length=255,
        default=NimbusConstants.PublishStatus.IDLE.value,
        choices=NimbusConstants.PublishStatus.choices,
    )
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=NimbusConstants.MAX_SLUG_LEN, unique=True)
    public_description = models.TextField(default="")
    risk_mitigation_link = models.URLField(max_length=255, blank=True)
    is_paused = models.BooleanField(default=False)
    proposed_duration = models.PositiveIntegerField(
        default=NimbusConstants.DEFAULT_PROPOSED_DURATION,
        validators=[MaxValueValidator(NimbusConstants.MAX_DURATION)],
    )
    proposed_enrollment = models.PositiveIntegerField(
        default=NimbusConstants.DEFAULT_PROPOSED_ENROLLMENT,
        validators=[MaxValueValidator(NimbusConstants.MAX_DURATION)],
    )
    population_percent = models.DecimalField(max_digits=7, decimal_places=4, default=0.0)
    total_enrolled_clients = models.PositiveIntegerField(default=0)
    firefox_min_version = models.CharField(
        max_length=255,
        choices=NimbusConstants.Version.choices,
        default=NimbusConstants.Version.NO_VERSION,
    )
    application = models.CharField(
        max_length=255,
        choices=NimbusConstants.Application.choices,
    )
    channel = models.CharField(
        max_length=255,
        choices=NimbusConstants.Channel.choices,
        default=NimbusConstants.Channel.NO_CHANNEL,
    )
    locales = models.ManyToManyField(Locale, blank=True)
    countries = models.ManyToManyField(Country, blank=True)
    projects = models.ManyToManyField(Project, blank=True)
    hypothesis = models.TextField(default=NimbusConstants.HYPOTHESIS_DEFAULT)
    primary_outcomes = ArrayField(models.CharField(max_length=255), default=list)
    secondary_outcomes = ArrayField(models.CharField(max_length=255), default=list)
    feature_config = models.ForeignKey(
        "NimbusFeatureConfig", blank=True, null=True, on_delete=models.CASCADE
    )
    targeting_config_slug = models.CharField(
        max_length=255,
        blank=True,
        default=NimbusConstants.TargetingConfig.NO_TARGETING,
    )
    reference_branch = models.OneToOneField(
        "NimbusBranch", blank=True, null=True, on_delete=models.CASCADE
    )
    published_dto = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    results_data = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    risk_partner_related = models.BooleanField(default=None, blank=True, null=True)
    risk_revenue = models.BooleanField(default=None, blank=True, null=True)
    risk_brand = models.BooleanField(default=None, blank=True, null=True)

    objects = NimbusExperimentManager()

    class Meta:
        verbose_name = "Nimbus Experiment"
        verbose_name_plural = "Nimbus Experiments"

    class Filters:
        IS_LAUNCH_QUEUED = Q(
            status=NimbusConstants.Status.DRAFT,
            status_next=NimbusConstants.Status.LIVE,
            publish_status=NimbusConstants.PublishStatus.APPROVED,
        )
        IS_LAUNCHING = Q(
            status=NimbusConstants.Status.DRAFT,
            status_next=NimbusConstants.Status.LIVE,
            publish_status=NimbusConstants.PublishStatus.WAITING,
        )
        IS_PAUSE_QUEUED = Q(
            status=NimbusConstants.Status.LIVE,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            is_paused=False,
        )
        IS_PAUSING = Q(
            status=NimbusConstants.Status.LIVE,
            publish_status=NimbusConstants.PublishStatus.WAITING,
            is_paused=False,
        )
        IS_END_QUEUED = Q(
            status=NimbusConstants.Status.LIVE,
            status_next=NimbusConstants.Status.COMPLETE,
            publish_status=NimbusConstants.PublishStatus.APPROVED,
        )
        IS_ENDING = Q(
            status=NimbusConstants.Status.LIVE,
            status_next=NimbusConstants.Status.COMPLETE,
            publish_status=NimbusConstants.PublishStatus.WAITING,
        )
        SHOULD_TIMEOUT = Q(IS_LAUNCHING | IS_ENDING)
        SHOULD_ALLOCATE_BUCKETS = Q(
            Q(status=NimbusConstants.Status.PREVIEW)
            | Q(publish_status=NimbusConstants.PublishStatus.APPROVED)
        )

    def __str__(self):
        return self.name

    def apply_lifecycle_state(self, lifecycle_state):
        for name, value in lifecycle_state.value.items():
            setattr(self, name, value)

    def get_absolute_url(self):
        return reverse("nimbus-detail", kwargs={"slug": self.slug})

    @property
    def experiment_url(self):
        return urljoin(
            "https://{host}".format(host=settings.HOSTNAME), self.get_absolute_url()
        )

    # This is the full JEXL expression processed by clients
    @property
    def targeting(self):
        expressions = []

        if self.application == self.Application.DESKTOP:
            if self.channel:
                expressions.append(
                    'browserSettings.update.channel == "{channel}"'.format(
                        channel=self.channel
                    )
                )
            if self.firefox_min_version:
                expressions.append(
                    "version|versionCompare('{version}') >= 0".format(
                        version=self.firefox_min_version
                    )
                )

            # TODO: Remove opt-out after Firefox 84 is the earliest supported Desktop
            expressions.append("'app.shield.optoutstudies.enabled'|preferenceValue")

        if self.targeting_config and self.targeting_config.targeting:
            expressions.append(self.targeting_config.targeting)

        #  If there is no targeting defined all clients should match, so we return "true"
        if len(expressions) == 0:
            return "true"

        return " && ".join(expressions)

    @property
    def application_config(self):
        if self.application:
            return self.APPLICATION_CONFIGS[self.application]

    @property
    def targeting_config(self):
        if self.targeting_config_slug:
            return self.TARGETING_CONFIGS[self.targeting_config_slug]

    @property
    def treatment_branches(self):
        branches = self.branches.order_by("id")
        if self.reference_branch:
            branches = branches.exclude(id=self.reference_branch.id)
        return list(branches)

    @property
    def start_date(self):
        start_changelogs = self.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        )
        if start_changelogs.exists():
            return start_changelogs.order_by("-changed_on").first().changed_on

    @property
    def end_date(self):
        end_changelogs = self.changes.filter(
            old_status=self.Status.LIVE, new_status=self.Status.COMPLETE
        )
        if end_changelogs.exists():
            return end_changelogs.order_by("-changed_on").first().changed_on

    @property
    def proposed_enrollment_end_date(self):
        if self.start_date and self.proposed_enrollment is not None:
            return (
                self.start_date + datetime.timedelta(days=self.proposed_enrollment)
            ).date()

    @property
    def proposed_end_date(self):
        if self.start_date and self.proposed_duration:
            return (
                self.start_date + datetime.timedelta(days=self.proposed_duration)
            ).date()

    @property
    def computed_end_date(self):
        return self.end_date or self.proposed_end_date

    @property
    def should_pause(self):
        if self.proposed_enrollment_end_date:
            return datetime.date.today() >= self.proposed_enrollment_end_date

    @property
    def should_end(self):
        if self.proposed_end_date:
            return datetime.date.today() >= self.proposed_end_date

    @property
    def monitoring_dashboard_url(self):
        def to_timestamp(date):
            return int(time.mktime(date.timetuple())) * 1000

        start_date = ""
        end_date = ""

        if self.start_date:
            start_date = to_timestamp(self.start_date - datetime.timedelta(days=1))

        if self.end_date:
            end_date = to_timestamp(self.end_date + datetime.timedelta(days=2))

        return settings.MONITORING_URL.format(
            slug=self.slug, from_date=start_date, to_date=end_date
        )

    @property
    def review_url(self):
        is_staging = "settings-writer.stage" in settings.KINTO_ADMIN_URL

        return "{base_url}/{collection_path}/{collection}/{review_path}".format(
            base_url=settings.KINTO_ADMIN_URL,
            collection_path="#/buckets/main-workspace/collections",
            collection=self.application_config.rs_experiments_collection,
            # TODO: Update when simple-review is on prod in remote settings
            review_path="simple-review" if is_staging else "records",
        )

    def delete_branches(self):
        self.reference_branch = None
        self.save()
        self.branches.all().delete()

    def allocate_bucket_range(self):
        existing_bucket_range = NimbusBucketRange.objects.filter(experiment=self)
        if existing_bucket_range.exists():
            existing_bucket_range.delete()

        NimbusIsolationGroup.request_isolation_group_buckets(
            self.feature_config.slug,
            self,
            int(
                self.population_percent / Decimal("100.0") * NimbusExperiment.BUCKET_TOTAL
            ),
        )

    def can_review(self, reviewer):
        if (
            settings.SKIP_REVIEW_ACCESS_CONTROL_FOR_DEV_USER
            and reviewer.email == settings.DEV_USER_EMAIL
        ):
            return True

        if self.publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
        ):
            review_request = self.changes.latest_review_request()
            return review_request and review_request.changed_by != reviewer
        return False

    # Results are available if enrollment is complete and
    # more than a week has passed after that.
    @property
    def results_ready(self):
        if self.proposed_enrollment_end_date:
            resultsReadyDate = self.proposed_enrollment_end_date + datetime.timedelta(
                days=NimbusConstants.DAYS_UNTIL_ANALYSIS
            )
            return datetime.date.today() >= resultsReadyDate

    @property
    def signoff_recommendations(self):
        return {
            # QA signoff is always recommended
            "qa_signoff": True,
            "vp_signoff": any(
                (self.risk_brand, self.risk_revenue, self.risk_partner_related)
            ),
            "legal_signoff": any((self.risk_revenue, self.risk_partner_related)),
        }

    @property
    def should_timeout(self):
        review_expired = (
            timezone.now() - self.changes.latest_change().changed_on
        ) >= datetime.timedelta(seconds=settings.KINTO_REVIEW_TIMEOUT)
        return review_expired and self.has_filter(self.Filters.SHOULD_TIMEOUT)


class NimbusBranch(models.Model):
    experiment = models.ForeignKey(
        NimbusExperiment,
        related_name="branches",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255, null=False)
    slug = models.SlugField(max_length=NimbusConstants.MAX_SLUG_LEN, null=False)
    description = models.TextField(blank=True, default="")
    ratio = models.PositiveIntegerField(default=1)
    feature_enabled = models.BooleanField(default=True)
    feature_value = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Nimbus Branch"
        verbose_name_plural = "Nimbus Branches"
        unique_together = (("slug", "experiment"),)

    def __str__(self):
        return self.name


class NimbusDocumentationLink(models.Model):
    experiment = models.ForeignKey(
        NimbusExperiment,
        related_name="documentation_links",
        on_delete=models.CASCADE,
    )
    title = models.CharField(
        max_length=255,
        null=False,
        choices=NimbusConstants.DocumentationLink.choices,
    )
    link = models.URLField(max_length=255, null=False)

    class Meta:
        verbose_name = "Nimbus Documentation Link"
        verbose_name_plural = "Nimbus Documentation Links"
        unique_together = (("title", "experiment"),)
        ordering = ("id",)

    def __str__(self):
        return f"{self.title} ({self.link})"


class NimbusIsolationGroup(models.Model):
    application = models.CharField(
        max_length=255, choices=NimbusExperiment.Application.choices
    )
    name = models.CharField(max_length=255)
    instance = models.PositiveIntegerField(default=1)
    total = models.PositiveIntegerField(default=NimbusConstants.BUCKET_TOTAL)

    class Meta:
        verbose_name = "Bucket IsolationGroup"
        verbose_name_plural = "Bucket IsolationGroups"
        unique_together = ("application", "name", "instance")
        ordering = ("name", "instance")

    def __str__(self):  # pragma: no cover
        return self.namespace

    @property
    def randomization_unit(self):
        return NimbusExperiment.APPLICATION_CONFIGS[self.application].randomization_unit

    @property
    def namespace(self):
        return f"{self.name}-{self.instance}"

    @classmethod
    def request_isolation_group_buckets(cls, name, experiment, count):
        query = cls.objects.filter(name=name, application=experiment.application)
        if query.exists():
            isolation_group = query.order_by("-instance").first()
        else:
            isolation_group = cls.objects.create(
                name=name, application=experiment.application
            )

        return isolation_group.request_buckets(experiment, count)

    def request_buckets(self, experiment, count):
        isolation_group = self
        start = 0

        if self.bucket_ranges.exists():
            highest_bucket = self.bucket_ranges.all().order_by("-start").first()
            if highest_bucket.end + count > self.total:
                isolation_group = NimbusIsolationGroup.objects.create(
                    name=self.name,
                    application=experiment.application,
                    instance=self.instance + 1,
                )
            else:
                start = highest_bucket.end + 1

        return NimbusBucketRange.objects.create(
            experiment=experiment,
            isolation_group=isolation_group,
            start=start,
            count=count,
        )


class NimbusBucketRange(models.Model):
    experiment = models.OneToOneField(
        NimbusExperiment, related_name="bucket_range", on_delete=models.CASCADE
    )
    isolation_group = models.ForeignKey(
        NimbusIsolationGroup,
        related_name="bucket_ranges",
        on_delete=models.CASCADE,
    )
    start = models.PositiveIntegerField()
    count = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Bucket Range"
        verbose_name_plural = "Bucket Ranges"

    def __str__(self):  # pragma: no cover
        return (
            f"{self.isolation_group}: {self.start}-{self.end}"
            f"/{self.isolation_group.total}"
        )

    @property
    def end(self):
        return self.start + self.count - 1


class NimbusFeatureConfig(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)
    slug = models.SlugField(
        max_length=NimbusConstants.MAX_SLUG_LEN, unique=True, null=False
    )
    description = models.TextField(blank=True, null=True)
    application = models.CharField(
        max_length=255,
        choices=NimbusConstants.Application.choices,
        blank=True,
        null=True,
    )
    owner_email = models.EmailField(blank=True, null=True)
    schema = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Nimbus Feature Config"
        verbose_name_plural = "Nimbus Feature Configs"

    def __str__(self):  # pragma: no cover
        return self.name


class NimbusChangeLogManager(models.Manager):
    def latest_change(self):
        return self.all().order_by("-changed_on").first()

    def latest_review_request(self):
        return (
            self.all()
            .filter(NimbusChangeLog.Filters.IS_REVIEW_REQUEST)
            .order_by("-changed_on")
        ).first()

    def latest_rejection(self):
        change = self.latest_change()
        if change and change.has_filter(NimbusChangeLog.Filters.IS_REJECTION):
            return change

    def latest_timeout(self):
        change = self.latest_change()
        if change and change.has_filter(NimbusChangeLog.Filters.IS_TIMEOUT):
            return change


class NimbusChangeLog(FilterMixin, models.Model):
    def current_datetime():
        return timezone.now()

    experiment = models.ForeignKey(
        NimbusExperiment,
        related_name="changes",
        on_delete=models.CASCADE,
    )
    changed_on = models.DateTimeField(default=current_datetime)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    old_status = models.CharField(
        max_length=255, blank=True, null=True, choices=NimbusExperiment.Status.choices
    )
    old_status_next = models.CharField(
        max_length=255, blank=True, null=True, choices=NimbusExperiment.Status.choices
    )
    old_publish_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=NimbusExperiment.PublishStatus.choices,
    )
    new_status = models.CharField(max_length=255, choices=NimbusExperiment.Status.choices)
    new_status_next = models.CharField(
        max_length=255, blank=True, null=True, choices=NimbusExperiment.Status.choices
    )
    new_publish_status = models.CharField(
        max_length=255, choices=NimbusExperiment.PublishStatus.choices
    )
    message = models.TextField(blank=True, null=True)
    experiment_data = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    published_dto_changed = models.BooleanField(default=False)

    objects = NimbusChangeLogManager()

    class Meta:
        verbose_name = "Nimbus Experiment Change Log"
        verbose_name_plural = "Nimbus Experiment Change Logs"
        ordering = ("changed_on",)

    class Filters:
        IS_REVIEW_REQUEST = Q(
            old_publish_status=NimbusExperiment.PublishStatus.IDLE,
            new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        IS_REJECTION = Q(
            Q(old_status=F("new_status")),
            old_publish_status__in=(
                NimbusExperiment.PublishStatus.REVIEW,
                NimbusExperiment.PublishStatus.WAITING,
            ),
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            published_dto_changed=False,
        )
        IS_TIMEOUT = Q(
            Q(old_status=F("new_status")),
            old_publish_status=NimbusExperiment.PublishStatus.WAITING,
            new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )

    class Messages:
        TIMED_OUT_IN_KINTO = "Timed Out"
        PUSHED_TO_KINTO = "Pushed to Kinto"
        UPDATED_IN_KINTO = "Updated in Kinto"
        DELETED_FROM_KINTO = "Deleted from Kinto"
        LIVE = "Experiment is now live!"
        PAUSED = "Enrollment was paused"
        COMPLETED = "Experiment is complete"

    def __str__(self):
        if self.message:
            return self.message
        else:
            return (
                f"{self.old_status} > {self.new_status} "
                f"by {self.changed_by} on {self.changed_on}"
            )


class NimbusEmail(models.Model):
    experiment = models.ForeignKey(
        NimbusExperiment,
        related_name="emails",
        on_delete=models.CASCADE,
    )
    type = models.CharField(max_length=255, choices=NimbusExperiment.EmailType.choices)
    sent_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nimbus Email"
        verbose_name_plural = "Nimbus Emails"

    def __str__(self):  # pragma: no cover
        return f"Email: {self.experiment} {self.type} on {self.sent_on}"
