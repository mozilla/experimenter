import copy
import datetime
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urljoin
from uuid import uuid4

import packaging
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Count, F, Q, QuerySet
from django.db.models.constraints import UniqueConstraint
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from experimenter.base import UploadsStorage
from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.constants import ChangeEventType, NimbusConstants
from experimenter.projects.models import Project
from experimenter.targeting.constants import TargetingConstants


class FilterMixin:
    def has_filter(self, query_filter):
        return type(self).objects.filter(id=self.id).filter(query_filter).exists()


class NimbusExperimentManager(models.Manager["NimbusExperiment"]):
    def with_related(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "locales",
                "languages",
                "countries",
                "bucket_range",
                "bucket_range__isolation_group",
                "reference_branch",
                "branches",
                "branches__feature_values",
                "branches__feature_values__feature_config",
                "feature_configs",
            )
        )

    def latest_changed(self):
        return super().get_queryset().order_by("-_updated_date_time")

    def with_owner_features(self):
        return (
            self.get_queryset()
            .prefetch_related(
                "owner", "feature_configs", "feature_configs__schemas", "projects"
            )
            .order_by("-_updated_date_time")
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


class NimbusExperimentBranchThrough(models.Model):
    parent_experiment = models.ForeignKey(
        "NimbusExperiment",
        on_delete=models.CASCADE,
        related_name="%(class)s_parent",
    )
    child_experiment = models.ForeignKey(
        "NimbusExperiment",
        on_delete=models.CASCADE,
        related_name="%(class)s_child",
    )
    branch_slug = models.SlugField(
        max_length=NimbusConstants.MAX_SLUG_LEN, null=True, blank=True
    )

    class Meta:
        abstract = True
        unique_together = ("parent_experiment", "child_experiment", "branch_slug")


class NimbusExperimentBranchThroughRequired(NimbusExperimentBranchThrough):  # noqa: DJ008
    pass


class NimbusExperimentBranchThroughExcluded(NimbusExperimentBranchThrough):  # noqa: DJ008
    pass


class NimbusExperiment(NimbusConstants, TargetingConstants, FilterMixin, models.Model):
    parent = models.ForeignKey["NimbusExperiment"](
        "experiments.NimbusExperiment", models.SET_NULL, blank=True, null=True
    )
    is_rollout = models.BooleanField("Is Experiment a Rollout Flag", default=False)
    is_archived = models.BooleanField("Is Experiment Archived Flag", default=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_nimbusexperiments",
    )
    status = models.CharField(
        "Status",
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
        "Publish Status",
        max_length=255,
        default=NimbusConstants.PublishStatus.IDLE,
        choices=NimbusConstants.PublishStatus.choices,
    )
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=NimbusConstants.MAX_SLUG_LEN, unique=True)
    public_description = models.TextField("Description", default="")
    risk_mitigation_link = models.URLField(
        "Risk Mitigation Link", max_length=255, blank=True
    )
    is_paused = models.BooleanField("Is Enrollment Paused Flag", default=False)
    is_rollout_dirty = models.BooleanField(
        "Approved Changes Flag", blank=False, null=False, default=False
    )
    proposed_duration = models.PositiveIntegerField(
        "Proposed Duration",
        default=NimbusConstants.DEFAULT_PROPOSED_DURATION,
        validators=[MaxValueValidator(NimbusConstants.MAX_DURATION)],
    )
    proposed_enrollment = models.PositiveIntegerField(
        "Proposed Enrollment Duration",
        default=NimbusConstants.DEFAULT_PROPOSED_ENROLLMENT,
        validators=[MaxValueValidator(NimbusConstants.MAX_DURATION)],
    )
    population_percent = models.DecimalField[Decimal](
        "Population Percent", max_digits=7, decimal_places=4, default=0.0
    )
    total_enrolled_clients = models.PositiveIntegerField(
        "Expected Number of Clients", default=0
    )
    firefox_min_version = models.CharField(
        "Minimum Firefox Version",
        max_length=255,
        default=NimbusConstants.Version.NO_VERSION,
        blank=True,
    )
    firefox_max_version = models.CharField(
        "Maximum Firefox Version",
        max_length=255,
        default=NimbusConstants.Version.NO_VERSION,
        blank=True,
    )
    application = models.CharField(
        "Application Type",
        max_length=255,
        choices=NimbusConstants.Application.choices,
    )
    channel = models.CharField(
        "Channel Type",
        max_length=255,
        choices=NimbusConstants.Channel.choices,
    )
    locales = models.ManyToManyField[Locale](
        Locale, blank=True, verbose_name="Supported Locales"
    )
    countries = models.ManyToManyField[Country](
        Country, blank=True, verbose_name="Supported Countries"
    )
    languages = models.ManyToManyField[Language](
        Language, blank=True, verbose_name="Supported Languages"
    )
    is_sticky = models.BooleanField("Sticky Enrollment Flag", default=False)
    projects = models.ManyToManyField[Project](
        Project, blank=True, verbose_name="Supported Projects"
    )
    hypothesis = models.TextField(
        "Hypothesis", default=NimbusConstants.HYPOTHESIS_DEFAULT
    )
    primary_outcomes = ArrayField(
        models.CharField(max_length=255),
        default=list,
        verbose_name="Primary Outcomes",
    )
    secondary_outcomes = ArrayField(
        models.CharField(max_length=255),
        default=list,
        verbose_name="Secondary Outcomes",
    )
    feature_configs = models.ManyToManyField["NimbusFeatureConfig"](
        "NimbusFeatureConfig", blank=True, verbose_name="Feature configurations"
    )
    warn_feature_schema = models.BooleanField("Feature Schema Warning", default=False)
    targeting_config_slug = models.CharField(
        "Targeting Configuration Slug",
        max_length=255,
        default=TargetingConstants.TargetingConfig.NO_TARGETING,
    )
    reference_branch = models.OneToOneField["NimbusBranch"](
        "NimbusBranch",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Reference Branch",
    )
    published_dto = models.JSONField[Dict[str, Any]](
        "Published DTO", encoder=DjangoJSONEncoder, blank=True, null=True
    )
    results_data = models.JSONField[Dict[str, Any]](
        "Results Data", encoder=DjangoJSONEncoder, blank=True, null=True
    )
    risk_partner_related = models.BooleanField(
        "Is a Partner Related Risk Flag", default=None, blank=True, null=True
    )
    risk_revenue = models.BooleanField(
        "Is a Revenue Risk Flag", default=None, blank=True, null=True
    )
    risk_brand = models.BooleanField(
        "Is a Brand Risk Flag", default=None, blank=True, null=True
    )
    conclusion_recommendation = models.CharField(
        "Recommended Conclusion",
        max_length=255,
        blank=True,
        null=True,
    )
    takeaways_metric_gain = models.BooleanField(
        "Takeaways Metric Gain Flag", default=False, blank=False, null=False
    )
    takeaways_gain_amount = models.TextField(
        "Takeaways Gain Amount", blank=True, null=True
    )
    takeaways_qbr_learning = models.BooleanField(
        "Takeaways QBR Learning", default=False, blank=False, null=False
    )
    takeaways_summary = models.TextField("Takeaways Summary", blank=True, null=True)
    _updated_date_time = models.DateTimeField(auto_now=True)
    is_first_run = models.BooleanField("Is First Run Flag", default=False)
    is_client_schema_disabled = models.BooleanField(
        "Is Client Schema Disabled Flag", default=False
    )

    _start_date = models.DateField("Start Date", blank=True, null=True)
    _enrollment_end_date = models.DateField("Enrollment End Date", blank=True, null=True)
    _end_date = models.DateField("End Date", blank=True, null=True)
    prevent_pref_conflicts = models.BooleanField(
        "Prevent Preference Conflicts Flag", blank=True, null=True, default=False
    )
    proposed_release_date = models.DateField(
        "Expected Release Date", blank=True, null=True
    )

    is_localized = models.BooleanField("Is Localized Flag", default=False)
    localizations = models.TextField("Localizations", blank=True, null=True)
    published_date = models.DateTimeField("Date First Published", blank=True, null=True)

    required_experiments = models.ManyToManyField["NimbusExperiment"](
        "NimbusExperiment",
        related_name="required_by",
        blank=True,
        verbose_name="Required Experiments",
        through=NimbusExperimentBranchThroughRequired,
        through_fields=("parent_experiment", "child_experiment"),
    )
    excluded_experiments = models.ManyToManyField["NimbusExperiment"](
        "NimbusExperiment",
        related_name="excluded_by",
        blank=True,
        verbose_name="Excluded Experiments",
        through=NimbusExperimentBranchThroughExcluded,
        through_fields=("parent_experiment", "child_experiment"),
    )
    qa_status = models.CharField(
        "QA Status",
        max_length=255,
        default=NimbusConstants.QAStatus.NOT_SET,
        choices=NimbusConstants.QAStatus.choices,
    )
    qa_comment = models.TextField("QA Comment", blank=True, null=True)
    subscribers = models.ManyToManyField(
        User,
        related_name="subscribed_nimbusexperiments",
        blank=True,
        verbose_name="Subscribers",
    )
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
            | Q(
                is_rollout=True,
                status=NimbusConstants.Status.LIVE,
                status_next=NimbusConstants.Status.LIVE,
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
        return urljoin(f"https://{settings.HOSTNAME}", self.get_absolute_url())

    def _get_targeting_min_version(self):
        expressions = []

        version_key = "version"
        if self.application != self.Application.DESKTOP:
            version_key = "app_version"

        min_version_supported = True
        if self.application in self.TARGETING_APPLICATION_SUPPORTED_VERSION:
            supported_version = self.TARGETING_APPLICATION_SUPPORTED_VERSION[
                self.application
            ]
            min_version_supported = NimbusExperiment.Version.parse(
                self.firefox_min_version
            ) >= NimbusExperiment.Version.parse(supported_version)

        if min_version_supported and self.firefox_min_version:
            expressions.append(
                f"{version_key}|versionCompare('{self.firefox_min_version}') >= 0"
            )

        return expressions

    def _get_targeting_max_version(self):
        expressions = []

        version_key = "version"
        if self.application != self.Application.DESKTOP:
            version_key = "app_version"

        max_version_supported = True
        if self.application in self.TARGETING_APPLICATION_SUPPORTED_VERSION:
            supported_version = self.TARGETING_APPLICATION_SUPPORTED_VERSION[
                self.application
            ]
            max_version_supported = NimbusExperiment.Version.parse(
                self.firefox_max_version
            ) >= NimbusExperiment.Version.parse(supported_version)

        if max_version_supported and self.firefox_max_version:
            # HACK: tweak the min version to better match max version pattern
            max_version = self.firefox_max_version.replace("!", "*")
            expressions.append(f"{version_key}|versionCompare('{max_version}') <= 0")

        return expressions

    def _get_targeting_pref_conflicts(self):
        prefs = []

        if self.prevent_pref_conflicts:
            for config in self.feature_configs.all():
                prefs.extend(config.schemas.get(version=None).sets_prefs)

        return prefs

    # This is the full JEXL expression processed by clients
    @property
    def targeting(self):
        if self.published_dto:
            return self.published_dto.get("targeting", self.PUBLISHED_TARGETING_MISSING)

        sticky_expressions = []
        expressions = []

        if self.targeting_config and self.targeting_config.targeting:
            sticky_expressions.append(self.targeting_config.targeting)

        is_desktop = self.application == self.Application.DESKTOP
        if is_desktop and self.channel:
            expressions.append(f'browserSettings.update.channel == "{self.channel}"')

        sticky_expressions.extend(self._get_targeting_min_version())
        expressions.extend(self._get_targeting_max_version())

        if locales := self.locales.all():
            locales = [locale.code for locale in sorted(locales, key=lambda l: l.code)]

            sticky_expressions.append(f"locale in {locales}")

        if languages := self.languages.all():
            languages = [
                language.code for language in sorted(languages, key=lambda l: l.code)
            ]

            sticky_expressions.append(f"language in {languages}")

        if countries := self.countries.all():
            countries = [
                country.code for country in sorted(countries, key=lambda c: c.code)
            ]
            sticky_expressions.append(f"region in {countries}")

        enrollments_map_key = "enrollments_map"
        if is_desktop:
            enrollments_map_key = "enrollmentsMap"

        if excluded_experiments := NimbusExperimentBranchThroughExcluded.objects.filter(
            parent_experiment=self
        ).order_by("id"):
            for excluded in excluded_experiments:
                if excluded.branch_slug:
                    sticky_expressions.append(
                        f"({enrollments_map_key}['{excluded.child_experiment.slug}'] "
                        f"== '{excluded.branch_slug}') == false"
                    )
                else:
                    sticky_expressions.append(
                        f"('{excluded.child_experiment.slug}' in enrollments) == false"
                    )

        if required_experiments := NimbusExperimentBranchThroughRequired.objects.filter(
            parent_experiment=self
        ).order_by("id"):
            for required in required_experiments:
                if required.branch_slug:
                    sticky_expressions.append(
                        f"{enrollments_map_key}['{required.child_experiment.slug}'] "
                        f"== '{required.branch_slug}'"
                    )
                else:
                    sticky_expressions.append(
                        f"'{required.child_experiment.slug}' in enrollments"
                    )

        if self.is_sticky and sticky_expressions:
            expressions.append(
                make_sticky_targeting_expression(
                    is_desktop, self.is_rollout, sticky_expressions
                )
            )
        else:
            expressions.extend(sticky_expressions)

        if prefs := self._get_targeting_pref_conflicts():
            expressions.append(
                make_sticky_targeting_expression(
                    is_desktop,
                    self.is_rollout,
                    (f"!('{pref}'|preferenceIsUserSet)" for pref in prefs),
                )
            )

        #  If there is no targeting defined all clients should match, so we return "true"
        return (
            " && ".join(f"({expression})" for expression in expressions)
            if expressions
            else "true"
        )

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
    def is_started(self):
        return self.status in (self.Status.LIVE, self.Status.COMPLETE)

    @property
    def start_date(self):
        if self._start_date is not None:
            return self._start_date

        if self.is_started:
            if (
                start_changelog := self.changes.all()
                .filter(
                    old_status=self.Status.DRAFT,
                    new_status=self.Status.LIVE,
                )
                .order_by("-changed_on")
                .first()
            ):
                self._start_date = start_changelog.changed_on.date()
                self.save()
                return self._start_date

    @property
    def release_date(self):
        if self.is_first_run:
            return self.proposed_release_date

    @property
    def enrollment_start_date(self):
        return self.release_date or self.start_date

    @property
    def launch_month(self):
        if self.enrollment_start_date is not None:
            return self.enrollment_start_date.strftime("%B")

    @property
    def end_date(self):
        if self._end_date is not None:
            return self._end_date

        if self.status == self.Status.COMPLETE:
            if (
                end_changelog := self.changes.all()
                .filter(old_status=self.Status.LIVE, new_status=self.Status.COMPLETE)
                .order_by("-changed_on")
                .first()
            ):
                self._end_date = end_changelog.changed_on.date()
                self.save()
                return self._end_date

    @property
    def proposed_enrollment_end_date(self):
        if (
            self.proposed_enrollment is not None
            and self.enrollment_start_date is not None
        ):
            return self.enrollment_start_date + datetime.timedelta(
                days=self.proposed_enrollment
            )

    @property
    def proposed_end_date(self):
        if self.proposed_duration is not None and self.enrollment_start_date is not None:
            return self.enrollment_start_date + datetime.timedelta(
                days=self.proposed_duration
            )

    @property
    def computed_enrollment_days(self):
        enrollment_start = self.enrollment_start_date
        if self._enrollment_end_date is not None and enrollment_start is not None:
            return (self._enrollment_end_date - enrollment_start).days

        if self.is_paused:
            if paused_changelogs := [
                c
                for c in self.changes.all().filter(
                    old_status=self.Status.LIVE,
                    new_status=self.Status.LIVE,
                    new_status_next=None,
                    new_publish_status=self.PublishStatus.IDLE,
                )
                if c.experiment_data is not None
                and "is_paused" in c.experiment_data
                and c.experiment_data["is_paused"]
            ]:
                paused_change = sorted(paused_changelogs, key=lambda c: c.changed_on)[-1]
                self._enrollment_end_date = paused_change.changed_on.date()
                self.save()
                return (paused_change.changed_on.date() - enrollment_start).days

        if self.end_date:
            return self.computed_duration_days

        return self.proposed_enrollment

    @property
    def computed_enrollment_end_date(self):
        if (
            self.computed_enrollment_days is not None
            and self.enrollment_start_date is not None
        ):
            return self.enrollment_start_date + datetime.timedelta(
                days=self.computed_enrollment_days
            )

    @property
    def actual_enrollment_end_date(self):
        return self._enrollment_end_date or None

    @property
    def computed_end_date(self):
        return self.end_date or self.proposed_end_date

    @property
    def enrollment_duration(self):
        if self.computed_end_date and self.enrollment_start_date is not None:
            return (
                self.enrollment_start_date.strftime("%Y-%m-%d")
                + " to "
                + self.computed_end_date.strftime("%Y-%m-%d")
            )
        return self.proposed_duration

    @property
    def computed_duration_days(self):
        if self.computed_end_date and self.enrollment_start_date is not None:
            return (self.computed_end_date - self.enrollment_start_date).days
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
    def is_enrollment_pause_pending(self):
        return self.is_paused and not self.is_paused_published

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
    def rollout_monitoring_dashboard_url(self):
        if self.is_rollout and (
            self.status
            in (NimbusExperiment.Status.LIVE, NimbusExperiment.Status.COMPLETE)
        ):
            return settings.ROLLOUT_MONITORING_URL.format(
                slug=self.slug.replace("-", "_")
            )

    @property
    def review_url(self):
        if self.application_config:
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
        keys = []
        if self.application_config:
            keys.append(self.application_config.slug)

        keys.extend(
            feature_config.slug
            for feature_config in self.feature_configs.all().order_by("slug")
        )

        if self.channel:
            keys.append(self.channel)

        if self.is_rollout:
            if self.targeting_config_slug:
                keys.append(self.targeting_config_slug)
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
    def feature_has_live_multifeature_experiments(self):
        matching = []
        live_experiments = NimbusExperiment.objects.filter(
            status=self.Status.LIVE,
            application=self.application,
        )
        if live_experiments.exists():
            feature_slugs = self.feature_configs.all().values_list("slug", flat=True)
            matching = (
                live_experiments.annotate(n_feature_configs=Count("feature_configs"))
                .filter(n_feature_configs__gt=1)
                .filter(feature_configs__slug__in=feature_slugs)
                .exclude(id=self.id)
                .values_list("slug", flat=True)
                .distinct()
                .order_by("slug")
            )
        return matching

    @property
    def excluded_live_deliveries(self):
        matching = []
        if self.excluded_experiments.exists():
            matching = (
                self.excluded_experiments.filter(
                    status=NimbusExperiment.Status.LIVE,
                    application=self.application,
                )
                .exclude(id=self.id)
                .values_list("slug", flat=True)
                .distinct()
                .order_by("slug")
            )
        return matching

    @property
    def live_experiments_in_namespace(self):
        experiment_ids = NimbusBucketRange.objects.filter(
            isolation_group__name=self.bucket_namespace,
            isolation_group__application=self.application,
        ).values_list("experiment_id", flat=True)
        return (
            NimbusExperiment.objects.filter(
                id__in=experiment_ids,
                status=NimbusExperiment.Status.LIVE,
            )
            .exclude(id=self.id)
            .values_list("slug", flat=True)
            .distinct()
            .order_by("slug")
        )

    @property
    def can_edit(self):
        return (
            (
                self.status == self.Status.DRAFT
                and self.publish_status == self.PublishStatus.IDLE
            )
            or (
                self.is_rollout
                and self.status == self.Status.LIVE
                and self.publish_status == self.PublishStatus.IDLE
            )
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
    def results_ready_date(self):
        if self.proposed_enrollment_end_date:
            return self.proposed_enrollment_end_date + datetime.timedelta(
                days=NimbusConstants.DAYS_UNTIL_ANALYSIS
            )

    @property
    def results_ready(self):
        if self.proposed_enrollment_end_date:
            results_ready_date = self.results_ready_date
            return datetime.date.today() >= results_ready_date

    @property
    def has_displayable_results(self):
        # True if self.results_data has weekly or overall results
        if self.results_data and "v2" in self.results_data:
            results_data = self.results_data["v2"]
            for window in ["overall", "weekly"]:
                if window in results_data:
                    enrollments = results_data[window].get("enrollments", {}).get("all")
                    if enrollments is not None:
                        return True

        return False

    @property
    def show_results_url(self):
        return self.has_displayable_results and self.results_ready and not self.is_rollout

    @property
    def results_expected_date(self):
        if not self.is_rollout:
            if self._enrollment_end_date:
                return self._enrollment_end_date + datetime.timedelta(
                    days=NimbusConstants.DAYS_UNTIL_ANALYSIS
                )
            else:
                return self.results_ready_date

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

    def clone(self, name, user, rollout_branch_slug=None, changed_on=None):
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
        cloned.is_rollout_dirty = False
        cloned.reference_branch = None
        cloned.proposed_release_date = None
        cloned.published_dto = None
        cloned.results_data = None
        cloned.takeaways_summary = None
        cloned.conclusion_recommendation = None
        cloned.takeaways_metric_gain = False
        cloned.takeaways_gain_amount = None
        cloned.takeaways_qbr_learning = False
        cloned._start_date = None
        cloned._end_date = None
        cloned._enrollment_end_date = None
        cloned.qa_status = NimbusExperiment.QAStatus.NOT_SET
        cloned.qa_comment = None
        cloned.save()

        if rollout_branch_slug:
            branch = self.branches.get(slug=rollout_branch_slug)
            cloned.reference_branch = branch.clone(cloned)
            cloned.is_rollout = True
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

        for (
            required_experiment_branch
        ) in NimbusExperimentBranchThroughRequired.objects.filter(parent_experiment=self):
            NimbusExperimentBranchThroughRequired.objects.create(
                parent_experiment=cloned,
                child_experiment=required_experiment_branch.child_experiment,
                branch_slug=required_experiment_branch.branch_slug,
            )

        for (
            excluded_experiment_branch
        ) in NimbusExperimentBranchThroughExcluded.objects.filter(parent_experiment=self):
            NimbusExperimentBranchThroughExcluded.objects.create(
                parent_experiment=cloned,
                child_experiment=excluded_experiment_branch.child_experiment,
                branch_slug=excluded_experiment_branch.branch_slug,
            )

        cloned.feature_configs.add(*self.feature_configs.all())
        cloned.countries.add(*self.countries.all())
        if self.application == self.Application.DESKTOP:
            cloned.locales.add(*self.locales.all())
        cloned.languages.add(*self.languages.all())
        cloned.projects.add(*self.projects.all())
        cloned.subscribers.remove(*self.subscribers.all())

        if rollout_branch_slug:
            generate_nimbus_changelog(
                cloned,
                user,
                f"Cloned from {self} with rollout branch {rollout_branch_slug}",
                changed_on,
            )
        else:
            generate_nimbus_changelog(cloned, user, f"Cloned from {self}", changed_on)

        return cloned

    def get_changelogs_by_date(self):
        # Inline import to prevent circular import
        from experimenter.experiments.changelog_utils import get_formatted_change_object

        changes_by_date = defaultdict(list)
        date_option = "%I:%M %p %Z"
        date_option = "%I:%M %p %Z"
        changelogs = list(
            self.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        for index, changelog in enumerate(changelogs[:-1]):
            current_data = changelog.experiment_data
            previous_data = changelogs[index + 1].experiment_data
            local_timestamp = timezone.localtime(changelog.changed_on)
            timestamp = local_timestamp.strftime(date_option)
            local_timestamp = timezone.localtime(changelog.changed_on)
            timestamp = local_timestamp.strftime(date_option)

            diff_fields = {
                field: {
                    "old_value": previous_data.get(field),
                    "new_value": current_data.get(field),
                }
                for field in current_data
                if (
                    field != "_updated_date_time"
                    and field != "published_dto"
                    and field != "status_next"
                    and current_data[field] != previous_data.get(field)
                )
            }

            for field, field_diff in diff_fields.items():
                change = get_formatted_change_object(
                    field, field_diff, changelog, timestamp
                )

                changes_by_date[changelog.changed_on.date()].append(change)

        if changelogs:
            creation_log = changelogs[-1]
            first_local_timestamp = timezone.localtime(creation_log.changed_on)
            first_timestamp = first_local_timestamp.strftime(date_option)
            if self.parent:
                message = (
                    f"{creation_log.changed_by} "
                    f"cloned this experiment from {self.parent.name}"
                )
            else:
                message = f"{creation_log.changed_by} created this experiment"
            change = {
                "event": ChangeEventType.CREATION.name,
                "event_message": message,
                "changed_by": creation_log.changed_by,
                "timestamp": first_timestamp,
            }
            changes_by_date[creation_log.changed_on.date()].append(change)

        transformed_changelogs = [
            {"date": date, "changes": changes}
            for date, changes in changes_by_date.items()
        ]

        return transformed_changelogs


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
    screenshot_id = uuid4()
    ext = filename.split(".")[-1].lower()
    return Path(screenshot.branch.experiment.slug) / f"{screenshot_id}.{ext}"


class NimbusBranchFeatureValue(models.Model):
    branch = models.ForeignKey(
        NimbusBranch, related_name="feature_values", on_delete=models.CASCADE
    )
    feature_config = models.ForeignKey["NimbusFeatureConfig"](
        "NimbusFeatureConfig", on_delete=models.CASCADE
    )
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
        # Note: Feature values are serialized as an array of dicts
        # and the ordering must always match at serialization/deserialization
        # time for validation, so we introduce a stable ordering
        # by feature config slug
        ordering = ["feature_config__slug"]

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

    def __str__(self):  # pragma: no cover
        return f"{self.branch}: {self.description}"

    def delete(self, *args, **kwargs):
        old_image_name = self.image.name if self.image and self.image.name else None
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
    name = models.CharField(max_length=2048)
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
        isolation_group = (
            cls.objects.filter(name=name, application=experiment.application)
            .order_by("-instance")
            .first()
        )
        if isolation_group is None:
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
    id: int
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
    enabled = models.BooleanField(default=True)

    def schemas_between_versions(
        self,
        min_version: packaging.version,
        max_version: Optional[packaging.version],
    ) -> QuerySet["NimbusVersionedSchema"]:
        return (
            self.schemas.filter(
                NimbusFeatureVersion.objects.between_versions_q(
                    min_version, max_version, prefix="version"
                )
            )
            .order_by("-version__major", "-version__minor", "-version__patch")
            .select_related("version")
        )

    @dataclass
    class VersionedSchemaRange:
        # The versioned schemas in the requested range, or a single element list
        # with an unversioned schema.
        schemas: list["NimbusVersionedSchema"]

        # If true, then this feature is unsupported in the entire version range.
        unsupported_in_range: bool

        # Any versions in the requested range that do not support the schema.
        unsupported_versions: list["NimbusFeatureVersion"]

    def get_versioned_schema_range(
        self,
        min_version: packaging.version,
        max_version: Optional[packaging.version],
    ) -> VersionedSchemaRange:
        unsupported_versions: list[NimbusFeatureVersion] = []

        assume_unversioned = False
        if min_supported_version := NimbusConstants.MIN_VERSIONED_FEATURE_VERSION.get(
            self.application
        ):
            min_supported_version = NimbusExperiment.Version.parse(min_supported_version)

            if min_supported_version > min_version:
                if max_version is not None and min_supported_version >= max_version:
                    # We will not have any NimbusVerionedSchemas in this
                    # version range. The best we can do is use the
                    # unversioned schema.
                    #
                    # TODO(#9869): warn the user that we don't have information
                    # about this interval.
                    assume_unversioned = True
                elif max_version is None or min_supported_version < max_version:
                    # If you're targeting a minimum version before we have
                    # versioned manifests without an upper bound, we'll use the
                    # min_supported_version as the minimum version for determing
                    # what NimbusVersionedSchemas to use.
                    #
                    # Using the unversioned schema in this case makes less
                    # sense, because we have *some* version information.
                    #
                    # TODO(#9869): warn the user that we don't have information
                    # about this interval.
                    min_version = min_supported_version
        else:
            # This application does not support versioned feature configurations.
            assume_unversioned = True

        if assume_unversioned:
            schemas = [self.schemas.get(version=None)]
        else:
            schemas = list(self.schemas_between_versions(min_version, max_version))

            if schemas:
                # Find all NimbusFeatureVersion objects between the min and max
                # version that are supported by *any* feature in the
                # application.
                #
                # If there is a version in this queryse that isn't present in
                # `schemas`, then we know that the feature is not supported in
                # that version.
                supported_versions = (
                    NimbusFeatureVersion.objects.filter(
                        NimbusFeatureVersion.objects.between_versions_q(
                            min_version, max_version
                        ),
                        schemas__feature_config__application=self.application,
                    )
                    .order_by("-major", "-minor", "-patch")
                    .distinct()
                )

                schemas_by_version = {schema.version: schema for schema in schemas}

                for application_version in supported_versions:
                    if application_version not in schemas_by_version:
                        unsupported_versions.append(application_version)
            elif self.schemas.filter(version__isnull=False).exists():
                # There are versioned schemas outside this range. This feature
                # is unsupported in this range.
                return NimbusFeatureConfig.VersionedSchemaRange(
                    schemas=[],
                    unsupported_in_range=True,
                    unsupported_versions=[],
                )
            else:
                # There are no verioned schemas for this feature. Fall back to
                # using unversioned schema.
                schemas = [self.schemas.get(version=None)]

        return NimbusFeatureConfig.VersionedSchemaRange(
            schemas=schemas,
            unsupported_in_range=False,
            unsupported_versions=unsupported_versions,
        )

    class Meta:
        verbose_name = "Nimbus Feature Config"
        verbose_name_plural = "Nimbus Feature Configs"
        unique_together = ("application", "slug")

    def __str__(self):  # pragma: no cover
        return self.name


class NimbusFeatureVersionManager(models.Manager["NimbusFeatureVersion"]):
    def between_versions_q(
        self,
        min_version: packaging.version.Version,
        max_version: Optional[packaging.version.Version],
        *,
        prefix: Optional[str] = None,
    ) -> Q:
        if prefix is not None:

            def prefixed(**kwargs: dict[str, Any]):
                return {f"{prefix}__{k}": v for k, v in kwargs.items()}

        else:

            def prefixed(**kwargs: dict[str, Any]):
                return kwargs

        # (a, b, c) >= (d, e, f)
        # := (a > b) | (a = b & d > e) | (a = b & d = e & c >= f)
        # == (a > b) | (a = b & (d > e | (d = e & c >= f)))

        # packaging.version.Version uses major.minor.micro, but
        # NimbusFeatureVersion uses major.minor.patch (semver).
        q = Q(**prefixed(major__gt=min_version.major)) | Q(
            **prefixed(major=min_version.major)
        ) & (
            Q(**prefixed(minor__gt=min_version.minor))
            | Q(**prefixed(minor=min_version.minor, patch__gte=min_version.micro))
        )

        if max_version is not None:
            # (a, b, c) < (d, e, f)
            # := (a < d) | (a == d & b < e) | (a == d & b == e & c < f)
            # == (a < d) | (a == d & (b < e | (b == e & c < f)))
            q &= Q(**prefixed(major__lt=max_version.major)) | Q(
                **prefixed(major=max_version.major)
            ) & (
                Q(**prefixed(minor__lt=max_version.minor))
                | Q(**prefixed(minor=max_version.minor, patch__lt=max_version.micro))
            )

        return q


class NimbusFeatureVersion(models.Model):
    major = models.IntegerField(null=False)
    minor = models.IntegerField(null=False)
    patch = models.IntegerField(null=False)

    objects = NimbusFeatureVersionManager()

    class Meta:
        verbose_name = "Nimbus Feature Version"
        verbose_name_plural = "Nimbus Feature Versions"
        unique_together = ("major", "minor", "patch")

    def __repr__(self):  # pragma: no cover
        return f"<NimbusFeatureVersion({self.major}, {self.minor}, {self.patch})>"

    def __str__(self):  # pragma: no cover
        return f"{self.major}.{self.minor}.{self.patch}"


class NimbusVersionedSchema(models.Model):
    feature_config = models.ForeignKey(
        NimbusFeatureConfig,
        related_name="schemas",
        on_delete=models.CASCADE,
    )
    version = models.ForeignKey(
        NimbusFeatureVersion,
        related_name="schemas",
        on_delete=models.CASCADE,
        null=True,
    )
    schema = models.TextField(blank=True, null=True)

    # Desktop-only
    sets_prefs = ArrayField(models.CharField(max_length=255, null=False, default=list))
    set_pref_vars = models.JSONField[Dict[str, str]](null=False, default=dict)
    is_early_startup = models.BooleanField(null=False, default=False)

    class Meta:
        verbose_name = "Nimbus Versioned Schema"
        verbose_name_plural = "Nimbus Versioned Schemas"
        unique_together = ("feature_config", "version")

    def __repr__(self):  # pragma: no cover
        return (
            f"<NimbusVersionedSchema(feature_config_id={self.feature_config_id}, "
            f"version={self.version})>"
        )

    def __str__(self):  # pragma: no cover
        as_str = f"{self.feature_config}"

        if self.version is not None:
            as_str += f" (version {self.version})"
        else:
            as_str += " (unversioned)"

        return as_str


class NimbusChangeLogManager(models.Manager["NimbusChangeLog"]):
    def latest_change(self):
        return self.all().order_by("-changed_on").first()

    def latest_review_request(self):
        return (
            self.all()
            .filter(
                NimbusChangeLog.Filters.IS_REVIEW_REQUEST
                | NimbusChangeLog.Filters.IS_UPDATE_REVIEW_REQUEST
            )
            .order_by("-changed_on")
        ).first()

    def latest_rejection(self):
        change = self.latest_change()
        if change and change.has_filter(
            NimbusChangeLog.Filters.IS_REJECTION
            | NimbusChangeLog.Filters.IS_UPDATE_REJECTION
        ):
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
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
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
    experiment_data = models.JSONField[Dict[str, Any]](
        encoder=DjangoJSONEncoder, blank=True, null=True
    )
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
        IS_UPDATE_REVIEW_REQUEST = Q(
            old_publish_status=NimbusExperiment.PublishStatus.IDLE,
            new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
            experiment_data__is_rollout_dirty=True,
        )
        IS_REJECTION = Q(
            Q(old_status=F("new_status")),
            old_publish_status__in=(
                NimbusExperiment.PublishStatus.REVIEW,
                NimbusExperiment.PublishStatus.WAITING,
            ),
            new_publish_status=(NimbusExperiment.PublishStatus.IDLE),
            new_status__in=(
                NimbusExperiment.Status.DRAFT,
                NimbusExperiment.Status.LIVE,
            ),
            published_dto_changed=False,
        )
        IS_UPDATE_REJECTION = Q(
            Q(old_status=F("new_status")),
            old_publish_status__in=(
                NimbusExperiment.PublishStatus.REVIEW,
                NimbusExperiment.PublishStatus.WAITING,
            ),
            new_publish_status__in=(NimbusExperiment.PublishStatus.IDLE,),
            published_dto_changed=False,
            experiment_data__is_rollout_dirty=True,
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
        return self.message or (
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


def make_sticky_targeting_expression(is_desktop, is_rollout, expressions):
    if is_desktop:
        if is_rollout:
            sticky_clause = "experiment.slug in activeRollouts"
        else:
            sticky_clause = "experiment.slug in activeExperiments"
    else:
        sticky_clause = "is_already_enrolled"

    expressions_joined = " && ".join(f"({expression})" for expression in expressions)

    return f"({sticky_clause}) || ({expressions_joined})"
