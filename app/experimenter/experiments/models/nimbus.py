import datetime
import time
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from experimenter.experiments.constants import NimbusConstants
from experimenter.projects.models import Project


class NimbusExperiment(NimbusConstants, models.Model):
    owner = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="owned_nimbusexperiments",
    )
    status = models.CharField(
        max_length=255,
        default=NimbusConstants.Status.DRAFT.value,
        choices=NimbusConstants.Status.choices,
    )
    name = models.CharField(max_length=255, unique=True, null=False)
    slug = models.SlugField(
        max_length=NimbusConstants.MAX_SLUG_LEN, unique=True, null=False
    )
    public_description = models.TextField(blank=True, null=True)
    is_paused = models.BooleanField(default=False)
    proposed_duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(NimbusConstants.MAX_DURATION)],
    )
    proposed_enrollment = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(NimbusConstants.MAX_DURATION)],
    )
    population_percent = models.DecimalField(
        max_digits=7, decimal_places=4, default=0.0, blank=True, null=True
    )
    total_enrolled_clients = models.PositiveIntegerField(default=0)
    firefox_min_version = models.CharField(
        max_length=255,
        choices=NimbusConstants.Version.choices,
        blank=True,
        null=True,
    )
    application = models.CharField(
        max_length=255,
        choices=NimbusConstants.Application.choices,
        blank=True,
        null=True,
    )
    channel = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=NimbusConstants.Channel.choices,
    )
    projects = models.ManyToManyField(Project, blank=True)
    hypothesis = models.TextField(
        default=NimbusConstants.HYPOTHESIS_DEFAULT, blank=True, null=True
    )
    probe_sets = models.ManyToManyField(
        "NimbusProbeSet", through="NimbusExperimentProbeSets"
    )
    feature_config = models.ForeignKey(
        "NimbusFeatureConfig", blank=True, null=True, on_delete=models.CASCADE
    )
    targeting_config_slug = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=NimbusConstants.TargetingConfig.choices,
    )
    reference_branch = models.OneToOneField(
        "NimbusBranch", blank=True, null=True, on_delete=models.CASCADE
    )

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
    def is_fenix_experiment(self):
        return self.application == self.Application.FENIX

    @property
    def targeting_config(self):
        if self.targeting_config_slug:
            return self.TARGETING_CONFIGS[self.targeting_config_slug]

    def latest_change(self):
        return self.changes.order_by("-changed_on").first()

    @property
    def treatment_branches(self):
        if self.reference_branch:
            return self.branches.exclude(id=self.reference_branch.id).order_by("id")
        else:
            return self.branches.order_by("id")

    @property
    def primary_probe_sets(self):
        return (
            self.probe_sets.filter(nimbusexperimentprobesets__is_primary=True)
            .order_by("id")
            .all()
        )

    @property
    def secondary_probe_sets(self):
        return (
            self.probe_sets.filter(nimbusexperimentprobesets__is_primary=False)
            .order_by("id")
            .all()
        )

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
    def proposed_end_date(self):
        if self.start_date and self.proposed_enrollment:
            return (
                self.start_date + datetime.timedelta(days=self.proposed_duration)
            ).date()

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


class NimbusBranch(models.Model):
    experiment = models.ForeignKey(
        NimbusExperiment,
        related_name="branches",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255, null=False)
    slug = models.SlugField(max_length=NimbusConstants.MAX_SLUG_LEN, null=False)
    description = models.TextField(default="")
    ratio = models.PositiveIntegerField(default=1)
    feature_enabled = models.BooleanField(default=True)
    feature_value = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Nimbus Branch"
        verbose_name_plural = "Nimbus Branches"
        unique_together = (("slug", "experiment"),)

    def __str__(self):
        return self.name


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
        unique_together = ("name", "instance")
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


class NimbusProbe(models.Model):
    kind = models.CharField(max_length=255, choices=NimbusConstants.ProbeKind.choices)
    name = models.CharField(max_length=255, unique=True, null=False)
    event_category = models.CharField(max_length=255)
    event_method = models.CharField(max_length=255, blank=True, null=True)
    event_object = models.CharField(max_length=255, blank=True, null=True)
    event_value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Nimbus Probe"
        verbose_name_plural = "Nimbus Probes"

    def __str__(self):  # pragma: no cover
        return self.name


class NimbusProbeSet(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)
    slug = models.SlugField(
        max_length=NimbusConstants.MAX_SLUG_LEN, unique=True, null=False
    )
    probes = models.ManyToManyField(NimbusProbe)

    class Meta:
        verbose_name = "Nimbus Probe Set"
        verbose_name_plural = "Nimbus Probe Sets"

    def __str__(self):  # pragma: no cover
        return self.name


class NimbusExperimentProbeSets(models.Model):
    experiment = models.ForeignKey(
        NimbusExperiment,
        on_delete=models.CASCADE,
    )
    probe_set = models.ForeignKey(NimbusProbeSet, on_delete=models.CASCADE)
    is_primary = models.BooleanField(null=False)

    class Meta:
        verbose_name = "Nimbus Experiment Probe Set"
        verbose_name_plural = "Nimbus Experiment Probe Sets"
        unique_together = ["experiment", "probe_set"]


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
