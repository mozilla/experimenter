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
from django.urls import reverse
from django.utils import timezone

from experimenter.experiments.constants import NimbusConstants
from experimenter.projects.models import Project


class NimbusExperimentManager(models.Manager):
    def launch_queue(self, application):
        return self.filter(status=NimbusExperiment.Status.REVIEW, application=application)

    def pause_queue(self, application):
        return self.filter(
            status=NimbusExperiment.Status.LIVE,
            is_paused=False,
            application=application,
            id__in=[
                experiment.id for experiment in self.all() if experiment.should_pause
            ],
        )

    def end_queue(self, application):
        return self.filter(
            status=NimbusExperiment.Status.LIVE,
            application=application,
            is_end_requested=True,
        )


class NimbusExperiment(NimbusConstants, models.Model):
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
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=NimbusConstants.MAX_SLUG_LEN, unique=True)
    public_description = models.TextField(default="")
    risk_mitigation_link = models.URLField(max_length=255, blank=True)
    is_paused = models.BooleanField(default=False)
    is_end_requested = models.BooleanField(default=False)
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
    projects = models.ManyToManyField(Project, blank=True)
    hypothesis = models.TextField(default=NimbusConstants.HYPOTHESIS_DEFAULT)
    primary_outcomes = ArrayField(models.CharField(max_length=255), default=list)
    secondary_outcomes = ArrayField(models.CharField(max_length=255), default=list)
    feature_config = models.ForeignKey(
        "NimbusFeatureConfig", blank=True, null=True, on_delete=models.CASCADE
    )
    targeting_config_slug = models.CharField(
        max_length=255,
        choices=NimbusConstants.TargetingConfig.choices,
        default=NimbusConstants.TargetingConfig.NO_TARGETING,
    )
    reference_branch = models.OneToOneField(
        "NimbusBranch", blank=True, null=True, on_delete=models.CASCADE
    )

    objects = NimbusExperimentManager()

    class Meta:
        verbose_name = "Nimbus Experiment"
        verbose_name_plural = "Nimbus Experiments"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("nimbus-detail", kwargs={"slug": self.slug})

    @property
    def experiment_url(self):
        return urljoin(
            "https://{host}".format(host=settings.HOSTNAME), self.get_absolute_url()
        )

    @property
    def is_desktop_experiment(self):
        return self.application == self.Application.DESKTOP

    @property
    def is_fenix_experiment(self):
        return self.application == self.Application.FENIX

    # This is the full JEXL expression processed by clients
    @property
    def targeting(self):
        expressions = []

        if self.is_desktop_experiment:
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
        if self.targeting_config:
            expressions.append(self.targeting_config.targeting)

        # TODO: Remove opt-out after Firefox 84 is the earliest supported Desktop
        if self.is_desktop_experiment:
            expressions.append("'app.shield.optoutstudies.enabled'|preferenceValue")

        #  If there is no targeting defined all clients should match, so we return "true"
        if len(expressions) == 0:
            return "true"

        return " && ".join(expressions)

    @property
    def targeting_config(self):
        if self.targeting_config_slug:
            return self.TARGETING_CONFIGS[self.targeting_config_slug]

    def latest_change(self):
        return self.changes.order_by("-changed_on").first()

    @property
    def treatment_branches(self):
        branches = self.branches.order_by("id")
        if self.reference_branch:
            branches = branches.exclude(id=self.reference_branch.id)
        return list(branches)

    @property
    def start_date(self):
        start_changelog = self.changes.filter(
            old_status=self.Status.ACCEPTED, new_status=self.Status.LIVE
        )
        if start_changelog.exists():
            return start_changelog.get().changed_on

    @property
    def end_date(self):
        end_changelog = self.changes.filter(
            old_status=self.Status.LIVE, new_status=self.Status.COMPLETE
        )
        if end_changelog.exists():
            return end_changelog.get().changed_on

    @property
    def proposed_enrollment_end_date(self):
        if self.start_date and self.proposed_enrollment:
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

    def delete_branches(self):
        self.reference_branch = None
        self.save()
        self.branches.all().delete()

    @property
    def should_allocate_bucket_range(self):
        return self.status in [
            NimbusExperiment.Status.PREVIEW,
            NimbusExperiment.Status.REVIEW,
        ]

    def allocate_bucket_range(self):
        existing_bucket_range = NimbusBucketRange.objects.filter(experiment=self)
        if existing_bucket_range.exists():
            existing_bucket_range.delete()

        NimbusIsolationGroup.request_isolation_group_buckets(
            self.slug,
            self,
            int(
                self.population_percent / Decimal("100.0") * NimbusExperiment.BUCKET_TOTAL
            ),
        )


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
        return NimbusExperiment.APPLICATION_BUCKET_RANDOMIZATION_UNIT[self.application]

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


class NimbusChangeLog(models.Model):
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
    new_status = models.CharField(max_length=255, choices=NimbusExperiment.Status.choices)
    message = models.TextField(blank=True, null=True)
    experiment_data = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)

    class Meta:
        verbose_name = "Nimbus Experiment Change Log"
        verbose_name_plural = "Nimbus Experiment Change Logs"
        ordering = ("changed_on",)

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
