from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator
from django.db import models

from experimenter.experiments.constants import ExperimentConstants
from experimenter.projects.models import Project


class NimbusExperiment(ExperimentConstants, models.Model):
    owner = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="owned_nimbusexperiments",
    )
    status = models.CharField(
        max_length=255,
        default=ExperimentConstants.STATUS_DRAFT,
        choices=ExperimentConstants.STATUS_CHOICES,
    )
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=255, unique=True, blank=False, null=False)
    public_description = models.TextField(blank=True, null=True)
    is_paused = models.BooleanField(default=False)
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
    firefox_min_version = models.CharField(
        max_length=255,
        choices=ExperimentConstants.VERSION_CHOICES,
        blank=True,
        null=True,
    )
    firefox_max_version = models.CharField(
        max_length=255,
        choices=ExperimentConstants.VERSION_CHOICES,
        blank=True,
        null=True,
    )
    firefox_channel = models.CharField(
        max_length=255,
        choices=ExperimentConstants.CHANNEL_CHOICES,
        blank=True,
        null=True,
    )
    projects = models.ManyToManyField(Project, blank=True)
    objectives = models.TextField(
        default=ExperimentConstants.OBJECTIVES_DEFAULT, blank=True, null=True
    )
    bugzilla_id = models.CharField(max_length=255, blank=True, null=True)

    features = ArrayField(
        models.CharField(
            max_length=255,
            blank=True,
            null=True,
            choices=ExperimentConstants.RAPID_FEATURE_CHOICES,
        ),
        default=list,
    )
    audience = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=ExperimentConstants.RAPID_AUDIENCE_CHOICES,
    )

    class Meta:
        verbose_name = "NimbusExperiment"
        verbose_name_plural = "NimbusExperiments"

    def __str__(self):
        return self.name


class NimbusBucketNamespace(models.Model):
    name = models.CharField(max_length=255)
    instance = models.PositiveIntegerField(default=1)
    total = models.PositiveIntegerField(default=ExperimentConstants.BUCKET_TOTAL)
    randomization_unit = models.CharField(
        max_length=255, default=ExperimentConstants.BUCKET_RANDOMIZATION_UNIT
    )

    class Meta:
        verbose_name = "Bucket Namespace"
        verbose_name_plural = "Bucket Namespaces"
        unique_together = ("name", "instance")
        ordering = ("name", "instance")

    def __str__(self):  # pragma: no cover
        return f"{self.name}-{self.instance}"

    @classmethod
    def request_namespace_buckets(cls, name, experiment, count):
        if cls.objects.filter(name=name).exists():
            namespace = cls.objects.filter(name=name).order_by("-instance").first()
        else:
            namespace = cls.objects.create(name=name)

        return namespace.request_buckets(experiment, count)

    def request_buckets(self, experiment, count):
        namespace = self
        start = 0

        if self.bucket_ranges.exists():
            highest_bucket = self.bucket_ranges.all().order_by("-start").first()
            if highest_bucket.end + count > self.total:
                namespace = NimbusBucketNamespace.objects.create(
                    name=self.name, instance=self.instance + 1
                )
            else:
                start = highest_bucket.end + 1

        return NimbusBucketRange.objects.create(
            experiment=experiment, namespace=namespace, start=start, count=count
        )


class NimbusBucketRange(models.Model):
    experiment = models.OneToOneField(
        NimbusExperiment, related_name="bucket_ranges", on_delete=models.CASCADE
    )
    namespace = models.ForeignKey(
        NimbusBucketNamespace,
        related_name="bucket_ranges",
        on_delete=models.CASCADE,
    )
    start = models.PositiveIntegerField()
    count = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Bucket Range"
        verbose_name_plural = "Bucket Ranges"

    def __str__(self):  # pragma: no cover
        return f"{self.namespace}: {self.start}-{self.end}/{self.namespace.total}"

    @property
    def end(self):
        return self.start + self.count - 1
