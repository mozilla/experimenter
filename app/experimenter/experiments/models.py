import copy
import datetime
import os.path
from decimal import Decimal
from urllib.parse import urljoin
from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import F, Max, Q
from django.db.models.constraints import UniqueConstraint
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from experimenter.base import UploadsStorage
from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.constants import NimbusConstants
from experimenter.projects.models import Project
from experimenter.targeting.constants import TargetingConstants


class FilterMixin:
    def has_filter(self, filter):
        return type(self).objects.filter(id=self.id).filter(filter).exists()


class NimbusExperimentManager(models.Manager):
    def latest_changed(self):
        return (
            NimbusExperiment.objects.all()
            .annotate(latest_change=Max("changes__changed_on"))
            .order_by("-latest_change")
        )

    def latest_with_related(self):
        return self.latest_changed().prefetch_related(
            "owner",
            "changes",
            "feature_configs",
        )

    def launch_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_LAUNCH_QUEUED,
            application__in=applications,
        )

    def update_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_UPDATE_QUEUED,
            application__in=applications,
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

    def waiting_to_update_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_UPDATING, application__in=applications
        )

    def waiting_to_end_queue(self, applications):
        return self.filter(
            NimbusExperiment.Filters.IS_ENDING, application__in=applications
        )


class NimbusExperiment(NimbusConstants, TargetingConstants, FilterMixin, models.Model):
    parent = models.ForeignKey(
        "experiments.NimbusExperiment", models.SET_NULL, blank=True, null=True
    )
    is_rollout = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="owned_nimbusexperiments",
    )
    status = models.CharField(
        max_length=255,
        default=NimbusConstants.Status.DRAFT,
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
        default=NimbusConstants.PublishStatus.IDLE,
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
        default=NimbusConstants.Version.NO_VERSION,
        blank=True,
    )
    firefox_max_version = models.CharField(
        max_length=255,
        default=NimbusConstants.Version.NO_VERSION,
        blank=True,
    )
    application = models.CharField(
        max_length=255,
        choices=NimbusConstants.Application.choices,
    )
    channel = models.CharField(
        max_length=255,
        choices=NimbusConstants.Channel.choices,
    )
    locales = models.ManyToManyField(Locale, blank=True)
    countries = models.ManyToManyField(Country, blank=True)
    languages = models.ManyToManyField(Language, blank=True)
    projects = models.ManyToManyField(Project, blank=True)
    hypothesis = models.TextField(default=NimbusConstants.HYPOTHESIS_DEFAULT)
    primary_outcomes = ArrayField(models.CharField(max_length=255), default=list)
    secondary_outcomes = ArrayField(models.CharField(max_length=255), default=list)
    feature_configs = models.ManyToManyField(
        "NimbusFeatureConfig",
        blank=True,
    )
    warn_feature_schema = models.BooleanField(default=False)
    targeting_config_slug = models.CharField(
        max_length=255,
        default=TargetingConstants.TargetingConfig.NO_TARGETING,
    )
    reference_branch = models.OneToOneField(
        "NimbusBranch", blank=True, null=True, on_delete=models.SET_NULL
    )
    published_dto = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    results_data = models.JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    risk_partner_related = models.BooleanField(default=None, blank=True, null=True)
    risk_revenue = models.BooleanField(default=None, blank=True, null=True)
    risk_brand = models.BooleanField(default=None, blank=True, null=True)
    conclusion_recommendation = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    takeaways_summary = models.TextField(blank=True, null=True)

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
        IS_UPDATE_QUEUED = Q(
            status=NimbusConstants.Status.LIVE,
            status_next=NimbusConstants.Status.LIVE,
            publish_status=NimbusConstants.PublishStatus.APPROVED,
        )
        IS_UPDATING = Q(
            status=NimbusConstants.Status.LIVE,
            status_next=NimbusConstants.Status.LIVE,
            publish_status=NimbusConstants.PublishStatus.WAITING,
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
        SHOULD_ALLOCATE_BUCKETS = Q(
            Q(status=NimbusConstants.Status.PREVIEW)
            | Q(
                status=NimbusConstants.Status.DRAFT,
                publish_status=NimbusConstants.PublishStatus.APPROVED,
            )
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

    def _get_targeting_versions(self):
        expressions = []

        version_key = "version"
        if self.application != self.Application.DESKTOP:
            version_key = "app_version"

        min_version_supported = True
        max_version_supported = True
        if self.application in self.TARGETING_APPLICATION_SUPPORTED_VERSION:
            supported_version = self.TARGETING_APPLICATION_SUPPORTED_VERSION[
                self.application
            ]
            min_version_supported = NimbusExperiment.Version.parse(
                self.firefox_min_version
            ) >= NimbusExperiment.Version.parse(supported_version)
            max_version_supported = NimbusExperiment.Version.parse(
                self.firefox_max_version
            ) >= NimbusExperiment.Version.parse(supported_version)

        if min_version_supported and self.firefox_min_version:
            expressions.append(
                f"{version_key}|versionCompare('{self.firefox_min_version}') >= 0"
            )

        if max_version_supported and self.firefox_max_version:
            # HACK: tweak the min version to better match max version pattern
            max_version = self.firefox_max_version.replace("!", "*")
            expressions.append(f"{version_key}|versionCompare('{max_version}') <= 0")

        return expressions

    # This is the full JEXL expression processed by clients
    @property
    def targeting(self):
        if self.published_dto:
            return self.published_dto.get("targeting", self.PUBLISHED_TARGETING_MISSING)

        expressions = []

        if self.targeting_config and self.targeting_config.targeting:
            expressions.append(self.targeting_config.targeting)

        if self.application == self.Application.DESKTOP:
            if self.channel:
                expressions.append(f'browserSettings.update.channel == "{self.channel}"')

            # TODO: Remove opt-out after Firefox 84 is the earliest supported Desktop
            expressions.append("'app.shield.optoutstudies.enabled'|preferenceValue")

        expressions.extend(self._get_targeting_versions())

        if self.locales.count():
            locales = [locale.code for locale in self.locales.all().order_by("code")]
            # TODO: Remove once UI for mobile get relased to support languages
            if self.application == self.Application.DESKTOP:
                expressions.append(f"locale in {locales}")
            else:
                iso_locales = {locale[:2] for locale in locales}
                iso_locales_expression = " || ".join(
                    [f"'{language}' in locale" for language in sorted(iso_locales)]
                )
                expressions.append(iso_locales_expression)

        if self.languages.count():
            languages = [
                language.code for language in self.languages.all().order_by("code")
            ]

            expressions.append(f"language in {languages}")

        if self.countries.count():
            countries = [
                country.code for country in self.countries.all().order_by("code")
            ]
            expressions.append(f"region in {countries}")

        #  If there is no targeting defined all clients should match, so we return "true"
        if len(expressions) == 0:
            return "true"

        return " && ".join([f"({expression})" for expression in expressions])

    @property
    def application_config(self):
        if self.application:
            return self.APPLICATION_CONFIGS[self.application]

    @property
    def targeting_config(self):
        if (
            self.targeting_config_slug is not None
            and self.targeting_config_slug in self.TARGETING_CONFIGS
        ):
            return self.TARGETING_CONFIGS[self.targeting_config_slug]

    @property
    def treatment_branches(self):
        branches = self.branches.order_by("id")
        if self.reference_branch:
            branches = branches.exclude(id=self.reference_branch.id)
        return list(branches)

    @property
    def start_date(self):
        start_changelogs = [
            c
            for c in self.changes.all()
            if c.old_status == NimbusExperiment.Status.DRAFT
            and c.new_status == NimbusExperiment.Status.LIVE
        ]
        if start_changelogs:
            return sorted(start_changelogs, key=lambda c: c.changed_on)[
                -1
            ].changed_on.date()

    @property
    def launch_month(self):
        if self.start_date:
            return self.start_date.strftime("%B")

    @property
    def end_date(self):
        changes = self.changes.all()
        end_changelogs = [
            c
            for c in changes
            if c.old_status == self.Status.LIVE and c.new_status == self.Status.COMPLETE
        ]
        if end_changelogs:
            return sorted(end_changelogs, key=lambda c: c.changed_on)[
                -1
            ].changed_on.date()

    @property
    def proposed_enrollment_end_date(self):
        if self.start_date and self.proposed_enrollment is not None:
            return self.start_date + datetime.timedelta(days=self.proposed_enrollment)

    @property
    def proposed_end_date(self):
        if self.start_date and self.proposed_duration is not None:
            return self.start_date + datetime.timedelta(days=self.proposed_duration)

    @property
    def computed_enrollment_days(self):
        paused_change = (
            self.changes.all()
            .filter(NimbusChangeLog.Filters.IS_APPROVED_PAUSE)
            .order_by("changed_on")
            .first()
        )
        if paused_change:
            return (paused_change.changed_on.date() - self.start_date).days
        if self.end_date:
            return self.computed_duration_days
        return self.proposed_enrollment

    @property
    def computed_end_date(self):
        if self.end_date:
            return self.end_date
        else:
            return self.proposed_end_date

    @property
    def enrollment_duration(self):
        if self.start_date:
            return (
                self.start_date.strftime("%Y-%m-%d")
                + " to "
                + self.computed_end_date.strftime("%Y-%m-%d")
            )
        else:
            return self.proposed_duration

    @property
    def computed_duration_days(self):
        if self.start_date:
            return (self.computed_end_date - self.start_date).days
        else:
            return self.proposed_duration

    @property
    def should_end(self):
        if self.proposed_end_date:
            return datetime.date.today() >= self.proposed_end_date

    @property
    def should_end_enrollment(self):
        if self.proposed_enrollment_end_date:
            return datetime.date.today() >= self.proposed_enrollment_end_date

    @property
    def is_paused_published(self):
        return bool(self.published_dto and self.published_dto.get("isEnrollmentPaused"))

    @property
    def monitoring_dashboard_url(self):
        start_date = (self.start_date or datetime.date.today()) - datetime.timedelta(
            days=1
        )

        if self.end_date:
            end_date = self.end_date + datetime.timedelta(days=2)
        else:
            # add a day to account for Looker data being in UTC
            end_date = datetime.date.today() + datetime.timedelta(days=1)

        return settings.MONITORING_URL.format(
            slug=self.slug,
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d"),
        )

    @property
    def review_url(self):
        return "{base_url}{collection_path}/{collection}/{review_path}".format(
            base_url=settings.KINTO_ADMIN_URL,
            collection_path="#/buckets/main-workspace/collections",
            collection=self.application_config.kinto_collection,
            review_path="simple-review",
        )

    def delete_branches(self):
        self.reference_branch = None
        self.save()
        self.branches.all().delete()

    @property
    def bucket_namespace(self):
        keys = [
            self.application_config.slug,
        ]

        for feature_config in self.feature_configs.all().order_by("slug"):
            keys.append(feature_config.slug)

        if self.channel:
            keys.append(self.channel)

        if self.is_rollout:
            keys.append("rollout")

        return "-".join(keys)

    def allocate_bucket_range(self):
        existing_bucket_range = NimbusBucketRange.objects.filter(experiment=self)
        if existing_bucket_range.exists():
            isolation_group = existing_bucket_range.get().isolation_group
            existing_bucket_range.delete()

            if not isolation_group.bucket_ranges.exists():
                NimbusIsolationGroup.objects.filter(id=isolation_group.id).delete()

        NimbusIsolationGroup.request_isolation_group_buckets(
            self.bucket_namespace,
            self,
            int(
                self.population_percent / Decimal("100.0") * NimbusExperiment.BUCKET_TOTAL
            ),
        )

    @property
    def can_edit(self):
        return (
            self.status == self.Status.DRAFT
            and self.publish_status == self.PublishStatus.IDLE
            and not self.is_archived
        )

    @property
    def can_archive(self):
        return (
            self.status
            in (NimbusExperiment.Status.DRAFT, NimbusExperiment.Status.COMPLETE)
            and self.publish_status == self.PublishStatus.IDLE
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
        return self.publish_status == self.PublishStatus.WAITING and review_expired

    def clone(self, name, user, rollout_branch_slug=None):
        # Inline import to prevent circular import
        from experimenter.experiments.changelog_utils import generate_nimbus_changelog

        cloned = copy.copy(self)

        cloned.id = None
        cloned.name = name
        cloned.slug = slugify(cloned.name)
        cloned.status = self.Status.DRAFT
        cloned.status_next = None
        cloned.publish_status = self.PublishStatus.IDLE
        cloned.owner = user
        cloned.parent = self
        cloned.is_archived = False
        cloned.is_paused = False
        cloned.reference_branch = None
        cloned.published_dto = None
        cloned.results_data = None
        cloned.takeaways_summary = None
        cloned.conclusion_recommendation = None
        cloned.save()

        if rollout_branch_slug:
            branch = self.branches.get(slug=rollout_branch_slug)
            cloned.reference_branch = branch.clone(cloned)
            cloned.proposed_duration = NimbusExperiment.DEFAULT_PROPOSED_DURATION
            cloned.proposed_enrollment = NimbusExperiment.DEFAULT_PROPOSED_ENROLLMENT
            cloned.population_percent = 0
            cloned.total_enrolled_clients = 0
            cloned.save()
        else:
            for branch in self.branches.all():
                branch.clone(cloned)

            if self.reference_branch:
                cloned.reference_branch = cloned.branches.get(
                    slug=self.reference_branch.slug
                )
                cloned.save()

        for link in self.documentation_links.all():
            link.id = None
            link.experiment = cloned
            link.save()

        cloned.feature_configs.add(*self.feature_configs.all())
        cloned.countries.add(*self.countries.all())
        cloned.locales.add(*self.locales.all())
        cloned.languages.add(*self.languages.all())

        if rollout_branch_slug:
            generate_nimbus_changelog(
                cloned,
                user,
                f"Cloned from {self} with rollout branch {rollout_branch_slug}",
            )
        else:
            generate_nimbus_changelog(cloned, user, f"Cloned from {self}")

        return cloned


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

    class Meta:
        verbose_name = "Nimbus Branch"
        verbose_name_plural = "Nimbus Branches"
        unique_together = (("slug", "experiment"),)
        ordering = ("slug",)

    def __str__(self):
        return f"{self.experiment}: {self.name}"

    def clone(self, to_experiment):
        cloned = copy.copy(self)
        cloned.id = None
        cloned.experiment = to_experiment
        cloned.save()

        screenshots = self.screenshots.all()
        for screenshot in screenshots:
            screenshot.clone(cloned)

        for feature_value in self.feature_values.all():
            feature_value.id = None
            feature_value.branch = cloned
            feature_value.save()

        return cloned


# Helper to ensure branch screenshot filenames have controlled unique paths
def nimbus_branch_screenshot_upload_to(screenshot, filename):
    id = uuid4()
    ext = filename.split(".")[-1].lower()
    return os.path.join(screenshot.branch.experiment.slug, f"{id}.{ext}")


class NimbusBranchFeatureValue(models.Model):
    branch = models.ForeignKey(
        NimbusBranch, related_name="feature_values", on_delete=models.CASCADE
    )
    feature_config = models.ForeignKey(
        "NimbusFeatureConfig", blank=True, null=True, on_delete=models.CASCADE
    )
    enabled = models.BooleanField(default=True)
    value = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Nimbus Branch Feature Value"
        verbose_name_plural = "Nimbus Branch Feature Values"
        constraints = (
            UniqueConstraint(
                fields=("branch", "feature_config"),
                name="unique_with_branch_and_feature",
                condition=Q(feature_config__isnull=False),
            ),
        )

    def __str__(self):  # pragma: no cover
        return f"{self.branch}: {self.feature_config}"


class NimbusBranchScreenshot(models.Model):
    branch = models.ForeignKey(
        NimbusBranch,
        related_name="screenshots",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        storage=UploadsStorage,
        upload_to=nimbus_branch_screenshot_upload_to,
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]

    def delete(self, *args, **kwargs):
        old_image_name = None
        if self.image and self.image.name:
            old_image_name = self.image.name

        super().delete(*args, **kwargs)

        if old_image_name and self.image.storage.exists(old_image_name):
            self.image.storage.delete(self.image.name)

    def save(self, *args, **kwargs):
        old_image_name = None
        if self.id:
            model = apps.get_model(self._meta.app_label, self._meta.object_name)
            existing = model.objects.get(id=self.id)
            if existing.image and existing.image.name:
                old_image_name = existing.image.name

        super().save(*args, **kwargs)

        if (
            old_image_name
            and old_image_name != self.image.name
            and self.image.storage.exists(old_image_name)
        ):
            self.image.storage.delete(old_image_name)

    def clone(self, to_branch):
        image_copy = ContentFile(self.image.read())
        image_copy.name = self.image.name

        cloned = copy.copy(self)
        cloned.id = None
        cloned.branch = to_branch
        cloned.image = image_copy
        cloned.save()
        return cloned


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
    name = models.CharField(max_length=255, null=False)
    slug = models.SlugField(max_length=NimbusConstants.MAX_SLUG_LEN, null=False)
    description = models.TextField(blank=True, null=True)
    application = models.CharField(
        max_length=255,
        choices=NimbusConstants.Application.choices,
        blank=True,
        null=True,
    )
    owner_email = models.EmailField(blank=True, null=True)
    schema = models.TextField(blank=True, null=True)
    read_only = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Nimbus Feature Config"
        verbose_name_plural = "Nimbus Feature Configs"
        unique_together = ("application", "slug")

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
        IS_APPROVED_PAUSE = Q(
            experiment_data__is_paused=True,
            new_status=NimbusExperiment.Status.LIVE,
            new_status_next=None,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

    class Messages:
        TIMED_OUT_IN_KINTO = "Timed Out"
        LAUNCHING_TO_KINTO = "Launching to Remote Settings"
        UPDATING_IN_KINTO = "Updating in Remote Settings"
        UPDATED_IN_KINTO = "Updated in Remote Settings"
        DELETING_FROM_KINTO = "Deleting from Remote Settings"
        REJECTED_FROM_KINTO = "Rejected from Remote Settings"
        LIVE = "Experiment is live"
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
