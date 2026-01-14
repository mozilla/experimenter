import copy
import datetime
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from itertools import chain, zip_longest
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode, urljoin
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
from django.db.models import Case, Count, F, Q, QuerySet, When
from django.db.models.constraints import UniqueConstraint
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.constants import (
    BucketRandomizationUnit,
    ChangeEventType,
    NimbusConstants,
    TargetingMultipleKintoCollectionsError,
)
from experimenter.metrics import MetricAreas
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.outcomes import Outcomes
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

    def for_collection(self, query, collection):
        return (e for e in query if e.kinto_collection == collection)

    def launch_queue(self, applications, collection):
        return self.for_collection(
            self.filter(
                NimbusExperiment.Filters.IS_LAUNCH_QUEUED,
                application__in=applications,
            ),
            collection,
        )

    def update_queue(self, applications, collection):
        return self.for_collection(
            self.filter(
                NimbusExperiment.Filters.IS_UPDATE_QUEUED,
                application__in=applications,
            ),
            collection,
        )

    def end_queue(self, applications, collection):
        return self.for_collection(
            self.filter(
                NimbusExperiment.Filters.IS_END_QUEUED,
                application__in=applications,
            ),
            collection,
        )

    def waiting(self, applications, collection):
        return self.for_collection(
            self.filter(
                publish_status=NimbusExperiment.PublishStatus.WAITING,
                application__in=applications,
            ),
            collection,
        )

    def waiting_to_launch_queue(self, applications, collection):
        return self.for_collection(
            self.filter(
                NimbusExperiment.Filters.IS_LAUNCHING, application__in=applications
            ),
            collection,
        )

    def waiting_to_update_queue(self, applications, collection):
        return self.for_collection(
            self.filter(
                NimbusExperiment.Filters.IS_UPDATING, application__in=applications
            ),
            collection,
        )

    def waiting_to_end_queue(self, applications, collection):
        return self.for_collection(
            self.filter(NimbusExperiment.Filters.IS_ENDING, application__in=applications),
            collection,
        )

    def with_merged_channel(self):
        return self.get_queryset().annotate(
            merged_channel=Case(
                When(Q(channel__isnull=False) & ~Q(channel=""), then=F("channel")),
                default=F("channels__0"),
                output_field=models.CharField(),
            )
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


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=16, default="#cccccc")

    def __str__(self):
        return self.name


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
    _firefox_min_version_parsed = ArrayField(
        models.IntegerField(),
        size=3,
        default=[0, 0, 0],
        verbose_name="Firefox Minimum Version (Parsed)",
        help_text="Parsed version as [major, minor, patch] for sorting",
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
    channels = ArrayField(
        models.CharField(max_length=255),
        default=list,
        verbose_name="Channels",
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
    exclude_locales = models.BooleanField(
        "Exclude Locales",
        default=False,
        help_text="If True, exclude the selected locales instead of including them",
    )
    exclude_countries = models.BooleanField(
        "Exclude Countries",
        default=False,
        help_text="If True, exclude the selected countries instead of including them",
    )
    exclude_languages = models.BooleanField(
        "Exclude Languages",
        default=False,
        help_text="If True, exclude the selected languages instead of including them",
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
    segments = ArrayField(
        models.CharField(max_length=255),
        default=list,
        verbose_name="Segments",
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
    published_dto = models.JSONField[dict[str, Any]](
        "Published DTO", encoder=DjangoJSONEncoder, blank=True, null=True
    )
    results_data = models.JSONField[dict[str, Any]](
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
    risk_message = models.BooleanField(
        "Is a Message Risk Flag", default=None, blank=True, null=True
    )
    conclusion_recommendations = models.JSONField(
        verbose_name="Conclusion Recommendations", blank=True, null=True, default=list
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
    next_steps = models.TextField("Next Steps", blank=True, null=True)
    project_impact = models.CharField(
        "Project Impact",
        max_length=255,
        blank=True,
        null=True,
        default=None,
        choices=NimbusConstants.ProjectImpact.choices,
    )
    is_first_run = models.BooleanField("Is First Run Flag", default=False)
    is_client_schema_disabled = models.BooleanField(
        "Is Client Schema Disabled Flag", default=False
    )

    # Cached dates
    _updated_date_time = models.DateTimeField(auto_now=True)
    _start_date = models.DateField("Start Date", blank=True, null=True)
    _enrollment_end_date = models.DateField("Enrollment End Date", blank=True, null=True)
    _computed_end_date = models.DateField("Computed End Date", blank=True, null=True)
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
    qa_signoff = models.BooleanField("QA Sign-off", default=False)
    vp_signoff = models.BooleanField("VP Sign-off", default=False)
    legal_signoff = models.BooleanField("Legal Sign-off", default=False)
    subscribers = models.ManyToManyField(
        User,
        related_name="subscribed_nimbusexperiments",
        blank=True,
        verbose_name="Subscribers",
    )
    enable_review_slack_notifications = models.BooleanField(
        "Enable Review Slack Notifications",
        default=True,
    )
    use_group_id = models.BooleanField(default=True)
    objects = NimbusExperimentManager()
    is_firefox_labs_opt_in = models.BooleanField(
        "Is Experiment a Firefox Labs Opt-In?", default=False
    )
    firefox_labs_title = models.TextField(
        "The title to display in Firefox Labs (Fluent ID)",
        blank=True,
        null=True,
    )
    firefox_labs_description = models.TextField(
        "The description to display in Firefox Labs (Fluent ID)",
        blank=True,
        null=True,
    )
    firefox_labs_description_links = models.TextField(
        "Firefox Labs Description Links",
        blank=True,
        null=True,
        default=None,
    )
    firefox_labs_group = models.CharField(
        "The group this should appear under in Firefox Labs",
        blank=True,
        null=True,
        max_length=255,
        choices=NimbusConstants.FirefoxLabsGroups.choices,
    )
    requires_restart = models.BooleanField(
        (
            "Does this experiment require a restart to take effect? "
            "Only used by Firefox Labs."
        ),
        default=False,
    )
    equal_branch_ratio = models.BooleanField(default=True)
    klaatu_status = models.BooleanField("Automated Validation Status", default=False)
    klaatu_recent_run_ids = ArrayField(
        models.BigIntegerField(
            "Recent Klaatu Run ID", blank=True, null=True, default=None
        ),
        blank=True,
        default=list,
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="experiments")
    qa_run_date = models.DateField("QA Run Date", blank=True, null=True, default=None)
    qa_run_test_plan_url = models.URLField(
        "QA Run Test Plan URL",
        max_length=500,
        blank=True,
        null=True,
        default=None,
    )
    qa_run_testrail_url = models.URLField(
        "QA Run TestRail URL",
        max_length=500,
        blank=True,
        null=True,
        default=None,
    )

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

    def save(self, *args, **kwargs):
        if self.firefox_min_version:
            try:
                parsed = NimbusConstants.Version.parse(self.firefox_min_version)
                self._firefox_min_version_parsed = [
                    parsed.major,
                    parsed.minor,
                    parsed.micro,
                ]
            except Exception:
                pass

        super().save(*args, **kwargs)

    def apply_lifecycle_state(self, lifecycle_state):
        for name, value in lifecycle_state.value.items():
            setattr(self, name, value)

    def get_absolute_url(self):
        return reverse("nimbus-ui-detail", kwargs={"slug": self.slug})

    def get_detail_url(self):
        return reverse("nimbus-ui-detail", kwargs={"slug": self.slug})

    def get_history_url(self):
        return reverse("nimbus-ui-history", kwargs={"slug": self.slug})

    def get_update_overview_url(self):
        return reverse("nimbus-ui-update-overview", kwargs={"slug": self.slug})

    def get_update_branches_url(self):
        return reverse("nimbus-ui-update-branches", kwargs={"slug": self.slug})

    def get_update_metrics_url(self):
        return reverse("nimbus-ui-update-metrics", kwargs={"slug": self.slug})

    def get_update_audience_url(self):
        return reverse("nimbus-ui-update-audience", kwargs={"slug": self.slug})

    def get_detail_preview_recipe_json_url(self):
        return f"{self.get_detail_url()}#preview-recipe-json"

    def get_results_url(self):
        return reverse("nimbus-ui-results", kwargs={"slug": self.slug})

    def get_new_results_url(self):
        return reverse("nimbus-ui-new-results", kwargs={"slug": self.slug})

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
            for feature_config in self.feature_configs.all():
                feature_prefs = feature_config.schemas.get(version=None).set_pref_vars
                feature_values = NimbusBranchFeatureValue.objects.filter(
                    branch__experiment=self, feature_config=feature_config
                ).values_list("value", flat=True)

                if feature_prefs and feature_values:
                    try:
                        branch_variables = {
                            key for value in feature_values for key in json.loads(value)
                        }
                    except json.JSONDecodeError:
                        continue

                    branch_prefs = {
                        feature_prefs[variable]
                        for variable in branch_variables
                        if variable in feature_prefs
                    }
                    prefs.extend(branch_prefs)

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

        if self.is_desktop and self.channels:
            channels = json.dumps(sorted(self.channels))
            expressions.append(f"browserSettings.update.channel in {channels}")

        sticky_expressions.extend(self._get_targeting_min_version())
        expressions.extend(self._get_targeting_max_version())

        if locales := self.locales.all():
            locales = [locale.code for locale in sorted(locales, key=lambda l: l.code)]
            locales_expression = f"locale in {locales}"
            if self.exclude_locales:
                locales_expression = f"({locales_expression}) != true"
            sticky_expressions.append(locales_expression)

        if languages := self.languages.all():
            languages = [
                language.code for language in sorted(languages, key=lambda l: l.code)
            ]
            languages_expression = f"language in {languages}"
            if self.exclude_languages:
                languages_expression = f"({languages_expression}) != true"
            sticky_expressions.append(languages_expression)

        if countries := self.countries.all():
            countries = [
                country.code for country in sorted(countries, key=lambda c: c.code)
            ]
            countries_expression = f"region in {countries}"
            if self.exclude_countries:
                countries_expression = f"({countries_expression}) != true"
            sticky_expressions.append(countries_expression)

        enrollments_map_key = "enrollments_map"
        if self.is_desktop:
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
            required_expressions = []
            for required in required_experiments:
                if required.branch_slug:
                    required_expressions.append(
                        f"{enrollments_map_key}['{required.child_experiment.slug}'] "
                        f"== '{required.branch_slug}'"
                    )
                else:
                    required_expressions.append(
                        f"'{required.child_experiment.slug}' in enrollments"
                    )
            required_expression = " || ".join([f"({e})" for e in required_expressions])
            sticky_expressions.append(f"({required_expression})")

        if self.is_sticky and sticky_expressions:
            expressions.append(
                make_sticky_targeting_expression(
                    self.is_desktop, self.is_rollout, sticky_expressions
                )
            )
        else:
            expressions.extend(sticky_expressions)

        if prefs := self._get_targeting_pref_conflicts():
            expressions.append(
                make_sticky_targeting_expression(
                    self.is_desktop,
                    self.is_rollout,
                    (f"!('{pref}'|preferenceIsUserSet)" for pref in sorted(prefs)),
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
    def is_desktop(self):
        return self.application == self.Application.DESKTOP

    @property
    def is_mobile(self):
        return self.Application.is_mobile(self.application)

    @property
    def is_draft(self):
        return (
            self.status == self.Status.DRAFT
            and self.publish_status == self.PublishStatus.IDLE
        )

    @property
    def is_review(self):
        return (
            self.status == self.Status.DRAFT
            and self.publish_status == self.PublishStatus.REVIEW
        )

    @property
    def is_review_timeline(self):
        return self.status in {
            self.Status.DRAFT,
            self.Status.PREVIEW,
        } and self.publish_status in {
            self.PublishStatus.REVIEW,
            self.PublishStatus.APPROVED,
            self.PublishStatus.WAITING,
        }

    @property
    def is_preview(self):
        return self.status == self.Status.PREVIEW

    @property
    def is_enrolling(self):
        return self.status == self.Status.LIVE and not self.is_paused_published

    @property
    def is_complete(self):
        return self.status == self.Status.COMPLETE

    @property
    def is_observation(self):
        return self.status == self.Status.LIVE and self.is_paused_published

    @property
    def is_started(self):
        return self.status in (self.Status.LIVE, self.Status.COMPLETE)

    @property
    def can_draft_to_preview(self):
        return self.is_draft and not self.is_review and self.can_publish_to_preview

    @property
    def can_draft_to_review(self):
        return self.can_draft_to_preview

    @property
    def can_preview_to_draft(self):
        return self.is_preview

    @property
    def can_preview_to_review(self):
        return self.is_preview

    def should_show_remote_settings_pending(self, reviewer):
        return self.publish_status in (
            self.PublishStatus.APPROVED,
            self.PublishStatus.WAITING,
        ) and self.can_review(reviewer)

    @property
    def rejection_block(self):
        rejection = self.changes.latest_rejection()
        if not rejection:
            return None

        flow_key = None
        if rejection.old_status == self.Status.DRAFT:
            flow_key = "LAUNCH_EXPERIMENT"
        elif rejection.old_status == self.Status.LIVE:
            if rejection.old_status_next == self.Status.LIVE:
                flow_key = "END_ENROLLMENT"
            else:
                flow_key = "END_EXPERIMENT"

        return {
            "action": NimbusUIConstants.ReviewRequestMessages[flow_key].value,
            "email": rejection.changed_by.email,
            "date": rejection.changed_on,
            "message": rejection.message,
        }

    def review_messages(self):
        if self.status_next == self.Status.COMPLETE and self.is_rollout:
            return NimbusUIConstants.ReviewRequestMessages.END_ROLLOUT.value
        elif self.status_next == self.Status.COMPLETE:
            return NimbusUIConstants.ReviewRequestMessages.END_EXPERIMENT.value
        elif self.is_paused:
            return NimbusUIConstants.ReviewRequestMessages.END_ENROLLMENT.value
        elif self.is_rollout and self.is_rollout_dirty:
            return NimbusUIConstants.ReviewRequestMessages.UPDATE_ROLLOUT.value
        elif self.is_rollout:
            return NimbusUIConstants.ReviewRequestMessages.LAUNCH_ROLLOUT.value
        else:
            return NimbusUIConstants.ReviewRequestMessages.LAUNCH_EXPERIMENT.value

    @property
    def remote_settings_pending_message(self):
        if self.publish_status in (
            self.PublishStatus.APPROVED,
            self.PublishStatus.WAITING,
        ):
            return self.review_messages()

    @property
    def should_show_timeout_message(self):
        return self.changes.latest_timeout()

    @property
    def should_show_end_enrollment(self):
        # If these conditions change then you must update
        # `LiveToEndEnrollmentForm.clean`.
        return self.is_enrolling and (not self.is_rollout or self.is_firefox_labs_opt_in)

    @property
    def should_show_end_experiment(self):
        return (
            self.status == self.Status.LIVE
            and self.publish_status != self.PublishStatus.REVIEW
        )

    @property
    def should_show_rollout_request_update(self):
        return self.status == self.Status.LIVE and self.is_rollout

    @property
    def is_end_experiment_requested(self):
        return (
            self.status == self.Status.LIVE
            and self.status_next == self.Status.COMPLETE
            and self.publish_status == self.PublishStatus.REVIEW
        )

    @property
    def is_rollout_update_requested(self):
        return (
            self.status == self.Status.LIVE
            and self.status_next == self.Status.LIVE
            and self.publish_status == self.PublishStatus.REVIEW
            and self.is_rollout
            and self.is_rollout_dirty
        )

    @property
    def latest_review_requested_by(self):
        review_request = self.changes.latest_review_request()
        if review_request:
            return review_request.changed_by.email

    @property
    def draft_date(self):
        if change := self.changes.all().order_by("changed_on").first():
            return change.changed_on.date()

    @property
    def preview_date(self):
        if change := (
            self.changes.filter(new_status=self.Status.PREVIEW)
            .order_by("changed_on")
            .first()
        ):
            return change.changed_on.date()

    @property
    def review_date(self):
        if change := (
            self.changes.filter(
                new_status=self.Status.DRAFT, new_publish_status=self.PublishStatus.REVIEW
            )
            .order_by("changed_on")
            .first()
        ):
            return change.changed_on.date()

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
    def days_since_enrollment_start(self):
        if self.enrollment_start_date is not None:
            return (datetime.date.today() - self.enrollment_start_date).days

    @property
    def enrollment_percent_completion(self):
        if self.days_since_enrollment_start is not None and self.computed_enrollment_days:
            percent = (
                self.days_since_enrollment_start / self.computed_enrollment_days
            ) * 100
            return min(round(percent), 100.0)

    @property
    def days_since_observation_start(self):
        if (
            enrollment_end_date := (
                self.actual_enrollment_end_date or self.computed_enrollment_end_date
            )
        ) is not None:
            return (datetime.date.today() - enrollment_end_date).days

    @property
    def observation_percent_completion(self):
        if (
            self.days_since_observation_start is not None
            and self.computed_observations_days
        ):
            percent = (
                self.days_since_observation_start / self.computed_observations_days
            ) * 100
            return min(round(percent), 100.0)

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
            proposed_observation_duration = (
                self.proposed_duration - self.proposed_enrollment
            )
            total_duration = self.computed_enrollment_days + proposed_observation_duration
            return self.enrollment_start_date + datetime.timedelta(days=total_duration)

    @property
    def computed_enrollment_days(self):
        enrollment_start = self.enrollment_start_date
        if self._enrollment_end_date is not None and enrollment_start is not None:
            return (self._enrollment_end_date - enrollment_start).days

        if self.is_paused:
            if last_changed_on := (
                self.changes.filter(
                    old_status=self.Status.LIVE,
                    new_status=self.Status.LIVE,
                    new_status_next=None,
                    new_publish_status=self.PublishStatus.IDLE,
                    experiment_data__isnull=False,
                    experiment_data__is_paused=True,
                )
                .order_by("changed_on")
                .values_list("changed_on")
                .last()
            ):
                self._enrollment_end_date = last_changed_on[0].date()
                self.save()
                return (self._enrollment_end_date - enrollment_start).days

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

    def _get_computed_end_date(self):
        return self.end_date or self.proposed_end_date

    def update_computed_end_date(self, end_date=None):
        self._computed_end_date = end_date or self._get_computed_end_date()
        self.save()

    @property
    def computed_end_date(self):
        if self.status == self.Status.DRAFT:
            return None

        if self._computed_end_date:
            if self.start_date is not None and self._computed_end_date >= self.start_date:
                return self._computed_end_date

        end_date = self._get_computed_end_date()
        self.update_computed_end_date(end_date)
        return end_date

    @property
    def computed_draft_days(self):
        if self.draft_date and self.preview_date is not None:
            return (self.preview_date - self.draft_date).days
        elif self.draft_date and self.review_date is not None:
            return (self.review_date - self.draft_date).days

    @property
    def computed_preview_days(self):
        if self.preview_date and self.review_date is not None:
            return (self.review_date - self.preview_date).days

    @property
    def computed_review_days(self):
        if self.review_date and self.enrollment_start_date is not None:
            return (self.enrollment_start_date - self.review_date).days

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
    def computed_observations_days(self):
        if (
            enrollment_end_date := (
                self.actual_enrollment_end_date or self.computed_enrollment_end_date
            )
        ) and self.computed_end_date:
            return (self.computed_end_date - enrollment_end_date).days

    @property
    def is_live_rollout(self):
        return self.is_rollout and (self.is_enrolling or self.is_observation)

    @property
    def is_missing_takeaway_info(self):
        return (
            self.is_complete
            and not (self.takeaways_summary and self.takeaways_summary.strip())
            and not self.conclusion_recommendations
        )

    def can_edit_overview(self):
        return self.is_draft

    def can_edit_branches(self):
        return self.is_draft

    def can_edit_metrics(self):
        return self.is_draft

    def can_edit_audience(self):
        return self.is_draft or (self.is_live_rollout and self.is_enrolling)

    def sidebar_links(self, current_path):
        return [
            {
                "title": "Summary",
                "link": self.get_detail_url(),
                "icon": "fa-regular fa-paper-plane",
                "active": current_path == self.get_detail_url(),
                "disabled": False,
            },
            {
                "title": "History",
                "link": self.get_history_url(),
                "icon": "fa-solid fa-network-wired",
                "active": current_path == self.get_history_url(),
                "disabled": False,
            },
            {
                "title": "Results",
                "link": self.get_results_url(),
                "icon": "fa-solid fa-chart-column",
                "active": current_path == self.get_results_url(),
                "disabled": self.disable_results_link,
                "new_results_url": self.get_new_results_url(),
                "subsections": self.results_sidebar_sections(),
            },
            {"title": "Edit", "is_header": True},
            {
                "title": "Overview",
                "link": self.get_update_overview_url(),
                "icon": "fa-solid fa-gear",
                "active": current_path == self.get_update_overview_url(),
                "disabled": not self.can_edit_overview(),
            },
            {
                "title": "Branches",
                "link": self.get_update_branches_url(),
                "icon": "fa-solid fa-layer-group",
                "active": current_path == self.get_update_branches_url(),
                "disabled": not self.can_edit_branches(),
            },
            {
                "title": "Metrics",
                "link": self.get_update_metrics_url(),
                "icon": "fa-solid fa-arrow-trend-up",
                "active": current_path == self.get_update_metrics_url(),
                "disabled": not self.can_edit_metrics(),
            },
            {
                "title": "Audience",
                "link": self.get_update_audience_url(),
                "icon": "fa-solid fa-user-group",
                "active": current_path == self.get_update_audience_url(),
                "disabled": not self.can_edit_audience(),
            },
        ]

    def results_sidebar_sections(self):
        return [
            {
                "title": "Overview",
                "subitems": [
                    {"title": "Hypothesis"},
                    {"title": "Branch overview"},
                    {"title": "Key takeaways"},
                    {"title": "Next steps"},
                    {"title": "Project Impact"},
                ],
            },
        ]

    def timeline(self):
        timeline_entries = [
            {
                "step": NimbusUIConstants.EXPERIMENT_ORDERING["Draft"],
                "label": self.Status.DRAFT,
                "date": self.draft_date,
                "is_active": self.is_draft,
                "days": self.computed_draft_days,
                "tooltip": NimbusUIConstants.TIMELINE_TOOLTIPS["Draft"],
            },
            {
                "step": NimbusUIConstants.EXPERIMENT_ORDERING["Preview"],
                "label": self.Status.PREVIEW,
                "date": self.preview_date,
                "is_active": self.is_preview,
                "days": self.computed_preview_days,
                "tooltip": NimbusUIConstants.TIMELINE_TOOLTIPS["Preview"],
            },
            {
                "step": NimbusUIConstants.EXPERIMENT_ORDERING["Review"],
                "label": self.PublishStatus.REVIEW,
                "date": self.review_date,
                "is_active": self.is_review_timeline,
                "days": self.computed_review_days,
                "tooltip": NimbusUIConstants.TIMELINE_TOOLTIPS["Review"],
            },
            {
                "step": NimbusUIConstants.EXPERIMENT_ORDERING["Enrollment"],
                "label": NimbusConstants.ENROLLMENT,
                "date": self.start_date,
                "is_active": self.is_enrolling,
                "days": self.computed_enrollment_days,
                "tooltip": NimbusUIConstants.TIMELINE_TOOLTIPS["Enrollment"],
            },
            {
                "step": NimbusUIConstants.EXPERIMENT_ORDERING["Complete"],
                "label": self.Status.COMPLETE,
                "date": self.computed_end_date,
                "is_active": self.is_complete,
                "days": self.computed_duration_days,
                "tooltip": NimbusUIConstants.TIMELINE_TOOLTIPS["Complete"],
            },
        ]
        if not self.is_rollout:
            timeline_entries.insert(
                4,
                {
                    "step": NimbusUIConstants.EXPERIMENT_ORDERING["Observation"],
                    "label": NimbusConstants.OBSERVATION,
                    "date": self._enrollment_end_date,
                    "is_active": self.is_observation,
                    "days": self.computed_observations_days,
                    "tooltip": NimbusUIConstants.TIMELINE_TOOLTIPS["Observation"],
                },
            )

        return timeline_entries

    def metric_has_errors(self, metric_slug, analysis_basis, segment):
        if self.results_data:
            for error, details in (
                self.results_data.get("v3", {}).get("errors", {}).items()
            ):
                if (
                    error == metric_slug
                    and details[0].get("analysis_basis") == analysis_basis
                    and details[0].get("segment") == segment
                ):
                    return True
        return False

    def get_metric_areas(
        self, analysis_basis, segment, reference_branch, window="overall"
    ):
        metric_areas = defaultdict(list)
        metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA] = []
        metric_areas[NimbusUIConstants.KPI_AREA] = self.get_kpi_metrics(
            analysis_basis, segment, reference_branch, window
        )

        metrics_metadata = {}
        if self.results_data:
            metrics_metadata = (
                self.results_data.get("v3", {}).get("metadata", {}).get("metrics", {})
            )

        all_outcome_metric_slugs = []
        for slug in chain(self.primary_outcomes, self.secondary_outcomes):
            outcome = Outcomes.get_by_slug_and_application(slug, self.application)
            metrics = outcome.metrics if outcome else []
            outcome_metrics = []

            for metric in metrics:
                formatted_metric = {
                    "slug": metric.slug,
                    "description": (
                        metric.description
                        if metric.description
                        else metrics_metadata.get(metric.slug, {}).get("description", "")
                    ),
                    "group": "other_metrics",
                    "friendly_name": (
                        metric.friendly_name
                        if metric.friendly_name
                        else metrics_metadata.get(metric.slug, {}).get(
                            "friendly_name", metric.slug
                        )
                    ),
                    "has_errors": self.metric_has_errors(
                        metric.slug, analysis_basis, segment
                    ),
                }
                if formatted_metric not in outcome_metrics:
                    outcome_metrics.append(formatted_metric)
                    all_outcome_metric_slugs.append(metric.slug)

            outcome_metrics.sort(key=lambda m: m["friendly_name"])
            metric_areas[outcome.friendly_name if outcome else slug] = outcome_metrics

        remaining_metrics = self.get_remaining_metrics_metadata(
            exclude_slugs=all_outcome_metric_slugs
        )
        grouped_metrics = []
        for metric in remaining_metrics:
            area = MetricAreas.get(self.application, metric["slug"])

            metric_areas[area].append(metric)
            grouped_metrics.append(metric)

        metric_areas[NimbusUIConstants.OTHER_METRICS_AREA] = [
            m for m in remaining_metrics if m not in grouped_metrics
        ]

        window_results = self.get_window_results(analysis_basis, segment, window)

        def is_metric_notable(slug, group):
            for branch_data in window_results.values():
                metric_data = (
                    branch_data.get("branch_data", {}).get(group, {}).get(slug, {})
                )
                for branch_significance in metric_data.get("significance", {}).values():
                    if (
                        "positive" in branch_significance.get(window, {}).values()
                        or "negative" in branch_significance.get(window, {}).values()
                    ):
                        return True
            return False

        for metrics in metric_areas.values():
            for metric in metrics:
                if (
                    is_metric_notable(metric["slug"], metric["group"])
                    and metric not in metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA]
                ):
                    metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA].append(metric)

        metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA].sort(
            key=lambda m: m["friendly_name"]
        )
        return metric_areas

    def get_remaining_metrics_metadata(
        self, exclude_slugs=None, analysis_basis=None, segment=None
    ):
        analysis_data = self.results_data.get("v3", {}) if self.results_data else {}
        other_metrics = analysis_data.get("other_metrics", {})
        metadata = analysis_data.get("metadata", {})
        metrics_metadata = metadata.get("metrics", {}) if metadata else {}
        defaults = []

        for group, default_metrics in other_metrics.items():
            for slug, metric_friendly_name in default_metrics.items():
                if exclude_slugs and slug in exclude_slugs:
                    continue
                defaults.append(
                    {
                        "slug": slug,
                        "description": metrics_metadata.get(slug, {}).get(
                            "description", ""
                        ),
                        "group": group,
                        "friendly_name": metric_friendly_name,
                        "has_errors": self.metric_has_errors(
                            slug, analysis_basis, segment
                        ),
                    }
                )

        defaults.sort(key=lambda m: m["friendly_name"])

        return defaults

    def get_branch_data(self, analysis_basis, selected_segment, window="overall"):
        window_results = self.get_window_results(analysis_basis, selected_segment, window)

        branch_data = []

        for branch in self.get_sorted_branches():
            slug = branch.slug
            participant_metrics = (
                window_results.get(slug, {})
                .get("branch_data", {})
                .get("other_metrics", {})
                .get("identity", {})
            )
            num_participants = (
                participant_metrics.get("absolute", {}).get("first", {}).get("point", 0)
            )

            branch_data.append(
                {
                    "slug": slug,
                    "name": branch.name,
                    "screenshots": branch.screenshots.all,
                    "description": branch.description,
                    "percentage": participant_metrics.get("percent"),
                    "num_participants": num_participants,
                },
            )

        return branch_data

    def get_metric_area_data(self, metrics, analysis_basis, segment, reference_branch):
        def get_window_metric_data(reference_branch, window_results, window):
            window_metric_data = {}

            for metric in metrics:
                slug = metric.get("slug")
                group = metric.get("group")

                branch_metrics = self.build_branch_metrics(
                    group, slug, window_results, reference_branch, window
                )

                window_metric_data[slug] = branch_metrics

            return window_metric_data

        metric_data = {
            "overall": get_window_metric_data(
                reference_branch,
                self.get_window_results(analysis_basis, segment, "overall"),
                "overall",
            ),
            "weekly": get_window_metric_data(
                reference_branch,
                self.get_window_results(analysis_basis, segment, "weekly"),
                "weekly",
            ),
        }

        metric_area_data = {"metrics": metrics, "data": metric_data}

        return metric_area_data

    def window_index_for_sort(self, point):
        wi = point.get("window_index")
        return int(wi) if wi is not None else 0

    def format_absolute_entries(self, metric_src, significance_map):
        absolute_data_list = metric_src.get("absolute", {}).get("all", [])
        absolute_data_list.sort(key=self.window_index_for_sort)
        abs_entries = []
        for i, data_point in enumerate(absolute_data_list):
            lower = data_point.get("lower")
            upper = data_point.get("upper")
            significance = significance_map.get(str(i + 1), "neutral")
            abs_entries.append(
                {"lower": lower, "upper": upper, "significance": significance}
            )
        return abs_entries

    def format_relative_entries(self, metric_src, significance_map, reference_branch):
        relative_data_list = (
            metric_src.get("relative_uplift", {}).get(reference_branch, {}).get("all", [])
        )
        relative_data_list.sort(key=self.window_index_for_sort)
        rel_entries = []
        for i, data_point in enumerate(relative_data_list):
            lower = data_point.get("lower")
            upper = data_point.get("upper")
            avg_rel_change = (
                abs(data_point.get("point")) if data_point.get("point") else None
            )
            significance = significance_map.get(str(i + 1), "neutral")
            rel_entries.append(
                {
                    "lower": lower,
                    "upper": upper,
                    "significance": significance,
                    "avg_rel_change": avg_rel_change,
                }
            )
        return rel_entries

    def build_branch_metrics(self, group, slug, window_results, reference_branch, window):
        branch_metrics = {}
        for branch in self.get_sorted_branches():
            branch_results = window_results.get(branch.slug, {}).get("branch_data", {})
            metric_src = branch_results.get(group, {}).get(slug, {})

            significance_map = (
                metric_src.get("significance", {})
                .get(reference_branch, {})
                .get(window, {})
            )

            abs_entries = self.format_absolute_entries(metric_src, significance_map)
            rel_entries = self.format_relative_entries(
                metric_src, significance_map, reference_branch
            )

            branch_metrics[branch.slug] = {
                "absolute": abs_entries,
                "relative": rel_entries,
            }

        return branch_metrics

    def get_kpi_metrics(
        self, analysis_basis, segment, reference_branch, window="overall"
    ):
        kpi_metrics = NimbusConstants.KPI_METRICS.copy()
        window_results = self.get_window_results(analysis_basis, segment, window)
        other_metrics = (
            (
                window_results.get(reference_branch, {})
                .get("branch_data", {})
                .get("other_metrics", {})
            )
            if isinstance(window_results, dict)
            else {}
        )

        if NimbusConstants.DAILY_ACTIVE_USERS in other_metrics:
            diff_metrics = other_metrics.get(NimbusConstants.DAILY_ACTIVE_USERS, {}).get(
                "difference", {}
            )
            for branch in diff_metrics:
                if len(diff_metrics.get(branch, {}).get("all", [])) > 0:
                    kpi_metrics.append(NimbusConstants.DAU_METRIC.copy())
                    break
        elif NimbusConstants.DAYS_OF_USE in other_metrics:
            if (
                len(
                    other_metrics.get(NimbusConstants.DAYS_OF_USE, {})
                    .get("absolute", {})
                    .get("all", [])
                )
                > 0
            ):
                kpi_metrics.append(NimbusConstants.DOU_METRIC.copy())

        for kpi in kpi_metrics:
            if self.metric_has_errors(kpi["slug"], analysis_basis, segment):
                kpi["has_errors"] = True

        return kpi_metrics

    def get_metric_data(
        self, analysis_basis, segment, reference_branch, window="overall"
    ):
        metric_areas = self.get_metric_areas(
            analysis_basis, segment, reference_branch, window
        )
        metric_data = {}

        for area, metrics in metric_areas.items():
            metric_data[area] = self.get_metric_area_data(
                metrics,
                analysis_basis,
                segment,
                reference_branch,
            )

        return metric_data

    def get_window_results(self, analysis_basis, segment, window="overall"):
        return (
            (
                self.results_data.get("v3", {})
                .get(window, {})
                .get(analysis_basis, {})
                .get(segment, {})
            )
            if self.results_data
            else {}
        )

    def get_max_metric_value(
        self,
        analysis_basis,
        segment,
        reference_branch,
        outcome_group,
        outcome_slug,
    ):
        overall_results = self.get_window_results(analysis_basis, segment, "overall")
        max_value = 0

        for branch in self.get_sorted_branches():
            if overall_results:
                for data_point in (
                    overall_results.get(branch.slug, {})
                    .get("branch_data", {})
                    .get(outcome_group, {})
                    .get(outcome_slug, {})
                    .get("relative_uplift", {})
                    .get(reference_branch, {})
                    .get("all", [])
                ):
                    lower = data_point.get("lower")
                    upper = data_point.get("upper")

                    max_value = max(max_value, abs(lower), abs(upper))

        return max_value

    def get_weekly_metric_data(self, analysis_basis, segment, reference_branch):
        all_metrics = self.get_metric_data(analysis_basis, segment, reference_branch)

        weekly_metric_data = {}

        for metric_data in all_metrics.values():
            metadata = metric_data.get("metrics", {})

            for metric_metadata in metadata:
                data = (
                    metric_data.get("data", {})
                    .get("weekly", {})
                    .get(metric_metadata["slug"], {})
                )
                weekly_data = {}

                for branch_slug, branch_data in data.items():
                    # Always produce a list of pairs by zipping absolute and relative
                    # When one side is missing or shorter, pad it with None so templates
                    # can iterate without complex conditionals.
                    abs_list = branch_data.get("absolute") or []
                    rel_list = branch_data.get("relative") or []

                    if abs_list or rel_list:
                        weekly_data[branch_slug] = list(
                            zip_longest(abs_list, rel_list, fillvalue=None)
                        )

                if weekly_data:
                    weekly_metric_data[metric_metadata["slug"]] = {
                        "has_weekly_data": True,
                        "data": weekly_data,
                    }
                else:
                    weekly_metric_data[metric_metadata["slug"]] = {
                        "has_weekly_data": False,
                        "data": {},
                    }

        return weekly_metric_data

    def get_weekly_dates(self):
        weekly_dates = []
        if not self.is_rollout:
            if self._enrollment_end_date:
                date = self._enrollment_end_date
                while (date + datetime.timedelta(days=7)) <= self.computed_end_date:
                    weekly_dates.append((date, date + datetime.timedelta(days=7)))
                    date += datetime.timedelta(days=7)

        return weekly_dates

    def get_sorted_branches(self):
        return (
            [
                self.reference_branch,
                *self.branches.exclude(id=self.reference_branch.id),
            ]
            if self.reference_branch
            else []
            # reference branch is always defined for created experiments, the empty
            # list is just a fallback for a specific test
        )

    @property
    def experiment_active_status(self):
        timeline = self.timeline()
        for item in timeline:
            if item["is_active"]:
                return item["step"]

    @property
    def should_end(self):
        if self.proposed_end_date:
            return datetime.date.today() >= self.proposed_end_date

    @property
    def should_end_enrollment(self):
        if self.proposed_enrollment_end_date:
            return datetime.date.today() >= self.proposed_enrollment_end_date

    @property
    def is_ready_for_attention(self):
        return (
            self.is_review
            or self.is_missing_takeaway_info
            or (not self.is_complete and (self.should_end_enrollment or self.should_end))
        )

    @property
    def is_paused_published(self):
        return bool(self.published_dto and self.published_dto.get("isEnrollmentPaused"))

    @property
    def is_enrollment_pause_pending(self):
        return self.is_paused and not self.is_paused_published

    @property
    def is_enrollment_pause_requested(self):
        return (
            self.status == self.Status.LIVE
            and self.status_next == self.Status.LIVE
            and self.is_enrollment_pause_pending
        )

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
            and (
                self.end_date is None
                or (
                    self.end_date
                    > datetime.date.today()
                    - datetime.timedelta(days=settings.ROLLOUT_MONITORING_EXPIRATION_DAYS)
                )
            )
        ):
            return settings.ROLLOUT_MONITORING_URL.format(
                slug=self.slug.replace("-", "_")
            )

    @property
    def required_experiments_branches(self):
        return NimbusExperimentBranchThroughRequired.objects.filter(
            parent_experiment=self
        )

    @property
    def excluded_experiments_branches(self):
        return NimbusExperimentBranchThroughExcluded.objects.filter(
            parent_experiment=self
        )

    @property
    def review_url(self):
        try:
            collection = self.kinto_collection
        except TargetingMultipleKintoCollectionsError:
            return None

        if collection:
            return "{base_url}{collection_path}/{collection}/{review_path}".format(
                base_url=settings.KINTO_ADMIN_URL,
                collection_path="#/buckets/main-workspace/collections",
                collection=collection,
                review_path="simple-review",
            )

    @property
    def audience_url(self):
        filters = [
            ("application", self.application),
        ]
        if self.channel:
            filters.append(("channel", self.channel))
        if self.countries.exists():
            filters.extend(
                [("countries", c.id) for c in self.countries.all().order_by("code")]
            )
        if self.locales.exists():
            filters.extend(
                [("locales", l.id) for l in self.locales.all().order_by("code")]
            )
        if self.languages.exists():
            filters.extend(
                [("languages", l.id) for l in self.languages.all().order_by("code")]
            )
        if self.targeting_config_slug:
            filters.append(("targeting_config_slug", self.targeting_config_slug))
        return f"{reverse('nimbus-list')}?{urlencode(filters)}"

    @property
    def can_publish_to_preview(self):
        if self.application_config:
            try:
                return (
                    self.kinto_collection
                    == self.application_config.default_kinto_collection
                )
            except TargetingMultipleKintoCollectionsError:
                return False

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

        if self.is_desktop and self.channels:
            keys.append("-".join(sorted(self.channels)))

        if self.channel:
            keys.append(self.channel)

        if self.is_rollout:
            if self.targeting_config_slug:
                keys.append(self.targeting_config_slug)
            keys.append("rollout")

        if self.is_desktop and self.use_group_id:
            keys.append(BucketRandomizationUnit.GROUP_ID)

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
            self.status == self.Status.DRAFT
            and self.publish_status == self.PublishStatus.IDLE
        ) or (
            (
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
    # more than a week (DAYS_UNTIL_ANALYSIS) has passed after that.
    @property
    def results_ready_date(self):
        if self.actual_enrollment_end_date:
            return self.actual_enrollment_end_date + datetime.timedelta(
                days=NimbusConstants.DAYS_UNTIL_ANALYSIS
            )
        if self.computed_enrollment_end_date:
            return self.computed_enrollment_end_date + datetime.timedelta(
                days=NimbusConstants.DAYS_UNTIL_ANALYSIS
            )

    @property
    def results_ready(self):
        if self.results_ready_date:
            results_ready_date = self.results_ready_date
            return datetime.date.today() >= results_ready_date

    @property
    def has_displayable_results(self):
        # True if self.results_data has weekly or overall results
        if self.results_data and "v3" in self.results_data:
            results_data = self.results_data["v3"]
            for window in ["overall", "weekly"]:
                if results_data.get(window):
                    for base in ["enrollments", "exposures"]:
                        base_results = results_data[window].get(base, {}).get("all")
                        if base_results is not None:
                            return True

        return False

    @property
    def has_exposures(self):
        # True if there are any exposures in the results data
        if self.results_data and "v3" in self.results_data:
            results_data = self.results_data["v3"]
            for window in ["overall", "weekly"]:
                if results_data.get(window):
                    exposure_data = results_data[window].get("exposures", {}).get("all")
                    if exposure_data is not None:
                        return True

        return False

    @property
    def show_results_url(self):
        # if there are results, show them! even if the dates are wrong
        # (the dates may have been overridden in metric-hub)
        return not self.is_rollout and self.has_displayable_results

    @property
    def disable_results_link(self):
        return not self.show_results_url

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
                (
                    self.risk_brand,
                    self.risk_revenue,
                    self.risk_partner_related,
                )
            ),
            "legal_signoff": any((self.risk_revenue, self.risk_partner_related)),
        }

    @property
    def home_type_choice(self):
        match (self.is_firefox_labs_opt_in, self.is_rollout):
            case (True, _):
                return NimbusConstants.HomeTypeChoices.LABS.label
            case (False, True):
                return NimbusConstants.HomeTypeChoices.ROLLOUT.label
            case (False, False):
                return NimbusConstants.HomeTypeChoices.EXPERIMENT.label

    @property
    def qa_status_icon_info(self):
        return NimbusConstants.QAStatus.get_icon_info(self.qa_status)

    @property
    def should_timeout(self):
        review_expired = (
            timezone.now() - self.changes.latest_change().changed_on
        ) >= datetime.timedelta(seconds=settings.KINTO_REVIEW_TIMEOUT)
        return self.publish_status == self.PublishStatus.WAITING and review_expired

    @property
    def rollout_conflict_warning(self):
        if not self.is_rollout:
            return None

        duplicate_rollout_count = (
            NimbusExperiment.objects.filter(
                status=self.Status.LIVE,
                channel=self.channel,
                application=self.application,
                targeting_config_slug=self.targeting_config_slug,
                feature_configs__in=self.feature_configs.all(),
                is_rollout=True,
            )
            .exclude(id=self.id)
            .count()
        )

        if duplicate_rollout_count > 0:
            return {
                "text": NimbusUIConstants.ERROR_ROLLOUT_BUCKET_EXISTS,
                "variant": "danger",
                "slugs": [],
                "learn_more_link": NimbusUIConstants.ROLLOUT_BUCKET_WARNING,
            }

    @property
    def rollout_version_warning(self):
        if not self.is_rollout or not self.firefox_min_version:
            return None

        min_required_version = (
            NimbusConstants.ROLLOUT_LIVE_RESIZE_MIN_SUPPORTED_VERSION.get(
                self.application
            )
        )

        parsed_required_version = NimbusExperiment.Version.parse(min_required_version)
        parsed_current_version = NimbusExperiment.Version.parse(self.firefox_min_version)

        if parsed_current_version < parsed_required_version:
            return {
                "text": NimbusConstants.ERROR_ROLLOUT_VERSION.format(
                    application=NimbusExperiment.Application(self.application).label,
                    version=parsed_required_version,
                ),
                "variant": "warning",
                "slugs": [],
                "learn_more_link": None,
            }

    @property
    def pref_targeting_rollout_collision_warning(self):
        if self.is_desktop and not self.is_rollout and self.prevent_pref_conflicts:
            colliding_experiments = NimbusExperiment.objects.filter(
                status=self.Status.LIVE,
                application=self.application,
                channels__overlap=self.channels,
                feature_configs__id__in=self.feature_configs.exclude(
                    schemas__set_pref_vars={}
                )
                .distinct()
                .values_list("id", flat=True),
                is_rollout=True,
            ).values_list("slug", flat=True)

            if colliding_experiments:
                return {
                    "text": NimbusUIConstants.PREF_TARGETING_WARNING,
                    "variant": "warning",
                    "slugs": list(colliding_experiments),
                    "learn_more_link": NimbusUIConstants.AUDIENCE_OVERLAP_WARNING,
                }

    @property
    def audience_overlap_warnings(self):
        warnings = []
        excluded_live_deliveries = ""
        if self.excluded_live_deliveries:
            excluded_live_deliveries = ", ".join(self.excluded_live_deliveries)

        feature_has_live_multifeature_experiments = ""
        if self.feature_has_live_multifeature_experiments:
            feature_has_live_multifeature_experiments = ", ".join(
                self.feature_has_live_multifeature_experiments
            )

        live_experiments_in_namespace = ""
        if self.live_experiments_in_namespace:
            live_experiments_in_namespace = ", ".join(self.live_experiments_in_namespace)

        overlapping_warnings = (
            feature_has_live_multifeature_experiments
            and live_experiments_in_namespace
            and feature_has_live_multifeature_experiments in live_experiments_in_namespace
        )

        if self.status in [NimbusConstants.Status.DRAFT, NimbusConstants.Status.PREVIEW]:
            if excluded_live_deliveries:
                warnings.append(
                    {
                        "text": NimbusUIConstants.EXCLUDING_EXPERIMENTS_WARNING,
                        "slugs": self.excluded_live_deliveries,
                        "variant": "warning",
                        "learn_more_link": NimbusUIConstants.AUDIENCE_OVERLAP_WARNING,
                    }
                )

            if live_experiments_in_namespace and not overlapping_warnings:
                warnings.append(
                    {
                        "text": NimbusUIConstants.LIVE_EXPERIMENTS_BUCKET_WARNING,
                        "slugs": self.live_experiments_in_namespace,
                        "variant": "warning",
                        "learn_more_link": NimbusUIConstants.AUDIENCE_OVERLAP_WARNING,
                    }
                )

            if feature_has_live_multifeature_experiments:
                warnings.append(
                    {
                        "text": NimbusUIConstants.LIVE_MULTIFEATURE_WARNING,
                        "slugs": self.feature_has_live_multifeature_experiments,
                        "variant": "warning",
                        "learn_more_link": NimbusUIConstants.AUDIENCE_OVERLAP_WARNING,
                    }
                )

            if rollout_conflict_warning := self.rollout_conflict_warning:
                warnings.append(rollout_conflict_warning)

            if rollout_version_warning := self.rollout_version_warning:
                warnings.append(rollout_version_warning)

            if pref_collision_warning := self.pref_targeting_rollout_collision_warning:
                warnings.append(pref_collision_warning)

            if self.is_desktop and not self.is_rollout and len(self.channels) > 1:
                warnings.append(
                    {
                        "text": NimbusUIConstants.EXPERIMENT_MULTICHANNEL_WARNING,
                        "slugs": [],
                        "variant": "warning",
                        "learn_more_link": "",
                    }
                )

        return warnings

    @property
    def has_results_errors(self):
        if self.results_data:
            for error in self.results_data.get("v3", {}).get("errors", {}).values():
                if error:
                    return True
        return False

    def get_invalid_fields_errors(self):
        from experimenter.experiments.api.v5.serializers import NimbusReviewSerializer

        serializer_data = NimbusReviewSerializer(self).data
        serializer = NimbusReviewSerializer(self, data=serializer_data)

        errors = {}
        if not serializer.is_valid():
            errors = serializer.errors

            if "excluded_experiments" in errors:
                errors["excluded_experiments_branches"] = errors.pop(
                    "excluded_experiments"
                )

            if "required_experiments" in errors:
                errors["required_experiments_branches"] = errors.pop(
                    "required_experiments"
                )

        return errors

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
        cloned.published_date = None
        cloned.results_data = None
        cloned.takeaways_summary = None
        cloned.next_steps = None
        cloned.project_impact = None
        cloned.conclusion_recommendations = []
        cloned.takeaways_metric_gain = False
        cloned.takeaways_gain_amount = None
        cloned.takeaways_qbr_learning = False
        cloned.use_group_id = True
        cloned._start_date = None
        cloned._end_date = None
        cloned._enrollment_end_date = None
        cloned._computed_end_date = None
        cloned.qa_status = NimbusExperiment.QAStatus.NOT_SET
        cloned.qa_comment = None
        cloned.klaatu_status = False
        cloned.klaatu_recent_run_id = None
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
        if self.is_desktop:
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

    @property
    def get_channel_display(self):
        if self.is_desktop and self.channels:
            return ", ".join(self.Channel(c).label for c in sorted(self.channels))
        elif self.channel:
            return self.Channel(self.channel).label

    @property
    def get_firefox_min_version_display(self):
        return self.firefox_min_version.replace("!", "0")

    @property
    def get_firefox_max_version_display(self):
        return self.firefox_max_version.replace("!", "0")

    @property
    def kinto_collection(self):
        # Note: this can throw if there are conflicting features targeting
        # different collections.
        if self.application_config:
            return self.application_config.get_kinto_collection_for_experiment(self)

    @property
    def conclusion_recommendation_labels(self):
        return [
            NimbusConstants.ConclusionRecommendation(rec).label
            for rec in self.conclusion_recommendations
        ]

    @property
    def recipe_json(self):
        from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer

        return (
            json.dumps(
                self.published_dto or NimbusExperimentSerializer(self).data,
                indent=2,
                sort_keys=True,
            )
            .replace("&&", "\n&&")  # Add helpful newlines to targeting
            .replace("\\n", "\n")  # Handle hard coded newlines in targeting
        )

    @property
    def qa_status_badge_class(self):
        if self.qa_status == self.QAStatus.RED:
            return "badge rounded-pill bg-danger"
        elif self.qa_status == self.QAStatus.YELLOW:
            return "badge rounded-pill bg-warning text-dark"
        elif self.qa_status == self.QAStatus.GREEN:
            return "badge rounded-pill bg-success"
        else:
            return "badge rounded-pill bg-secondary"

    @property
    def notification_emails(self):
        emails = chain(
            [self.owner.email],
            self.subscribers.values_list("email", flat=True),
            self.feature_configs.values_list("subscribers__email", flat=True),
        )
        return list({email for email in emails if email})


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
    firefox_labs_title = models.TextField(
        "An optional string containing the Fluent ID for the title of the opt-in",
        blank=True,
        null=True,
    )

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
    return Path(screenshot.branch.experiment.slug, f"{screenshot_id}.{ext}")


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

    @property
    def allow_coenrollment(self):
        min_version = NimbusExperiment.Version.parse(
            self.branch.experiment.firefox_min_version
        )
        max_version = None
        if self.branch.experiment.firefox_max_version:
            max_version = NimbusExperiment.Version.parse(
                self.branch.experiment.firefox_max_version
            )
        schemas = self.feature_config.get_versioned_schema_range(
            min_version,
            max_version,
        ).schemas
        return all(schema.allow_coenrollment for schema in schemas)

    @property
    def unversioned_schema(self):
        try:
            return self.feature_config.schemas.get(version=None).schema
        except NimbusVersionedSchema.DoesNotExist:
            return None


class NimbusBranchScreenshot(models.Model):
    branch = models.ForeignKey(
        NimbusBranch,
        related_name="screenshots",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
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
        if self.bucket_ranges.filter(
            experiment__use_group_id=True,
            experiment__application=NimbusExperiment.Application.DESKTOP,
        ).exists():
            return BucketRandomizationUnit.GROUP_ID
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
    subscribers = models.ManyToManyField(
        User,
        related_name="subscribed_nimbus_features",
        blank=True,
        verbose_name="Subscribers",
    )

    class Meta:
        verbose_name = "Nimbus Feature Config"
        verbose_name_plural = "Nimbus Feature Configs"
        unique_together = ("application", "slug")

    def __str__(self):  # pragma: no cover
        return f"{self.name} ({self.application})"

    def schemas_between_versions(
        self,
        min_version: packaging.version.Version,
        max_version: Optional[packaging.version.Version],
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
        # The minimum version of the range.
        min_version: packaging.version.Version

        # The maximum version of the range.
        max_version: Optional[packaging.version.Version]

        # The versioned schemas in the requested range, or a single element list
        # with an unversioned schema.
        schemas: list["NimbusVersionedSchema"]

        # If true, then this feature is unsupported in the entire version range.
        unsupported_in_range: bool

        # Any versions in the requested range that do not support the schema.
        unsupported_versions: list["NimbusFeatureVersion"]

    def get_versioned_schema_range(
        self,
        min_version: packaging.version.Version,
        max_version: Optional[packaging.version.Version],
    ) -> VersionedSchemaRange:
        unsupported_versions: list[NimbusFeatureVersion] = []

        assume_unversioned = False
        if min_supported_version := NimbusConstants.MIN_VERSIONED_FEATURE_VERSION.get(
            self.application
        ):
            min_supported_version = NimbusExperiment.Version.parse(min_supported_version)

            if min_supported_version > min_version:
                if max_version is not None and min_supported_version > max_version:
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
                    min_version=min_version,
                    max_version=max_version,
                    schemas=[],
                    unsupported_in_range=True,
                    unsupported_versions=[],
                )
            else:
                # There are no verioned schemas for this feature. Fall back to
                # using unversioned schema.
                schemas = [self.schemas.get(version=None)]

        return NimbusFeatureConfig.VersionedSchemaRange(
            min_version=min_version,
            max_version=max_version,
            schemas=schemas,
            unsupported_in_range=False,
            unsupported_versions=unsupported_versions,
        )


class NimbusFeatureVersionManager(models.Manager["NimbusFeatureVersion"]):
    def between_versions_q(
        self,
        min_version: packaging.version.Version,
        max_version: Optional[packaging.version.Version],
        *,
        prefix: Optional[str] = None,
    ) -> Q:
        """Return a query object that can be used to select all versions between lower and
        upper bounds (inclusive).

        Args:
            min_version:
                The lower bound (inclusive).

            max_version:
                The upper bound (inclusive).

            prefix:
                An optional prefix to prepend to the field names. This allows the Q object
                to be used by related models.

        Returns:
            The query object.
        """
        if prefix is not None:

            def prefixed(**kwargs: dict[str, Any]):
                return {f"{prefix}__{k}": v for k, v in kwargs.items()}

        else:

            def prefixed(**kwargs: dict[str, Any]):
                return kwargs

        # (a, b, c) >= (d, e, f)
        # := (a > d) | (a == d & b > e) | (a == d & b == e & c >= f)
        # == (a > d) | (a == d & (b > e | (b == e & c >= f)

        # packaging.version.Version uses major.minor.micro, but
        # NimbusFeatureVersion uses major.minor.patch (semver).
        q = Q(**prefixed(major__gt=min_version.major)) | (
            Q(**prefixed(major=min_version.major))
            & (
                Q(**prefixed(minor__gt=min_version.minor))
                | Q(**prefixed(minor=min_version.minor, patch__gte=min_version.micro))
            )
        )

        if max_version is not None:
            # (a, b, c) <= (d, e, f)
            # := (a < d) | (a == d & b < e) | (a = d & b == e & c <= f)
            # == (a < d) | (a == d & (b < e | (b == e & c <= f)))
            q &= Q(**prefixed(major__lt=max_version.major)) | (
                Q(**prefixed(major=max_version.major))
                & (
                    Q(**prefixed(minor__lt=max_version.minor))
                    | Q(**prefixed(minor=max_version.minor, patch__lte=max_version.micro))
                )
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

    def as_packaging_version(self) -> packaging.version.Version:
        return packaging.version.parse(str(self))


class NimbusVersionedSchemaManager(models.Manager["NimbusVersionedSchema"]):
    def with_version_ordering(self, descending=False):
        """Order schemas by semantic version (major.minor.patch)."""
        if descending:
            return self.order_by("-version__major", "-version__minor", "-version__patch")
        return self.order_by("version__major", "version__minor", "version__patch")


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
    allow_coenrollment = models.BooleanField(null=False, default=False)

    # Desktop-only
    set_pref_vars = models.JSONField[dict[str, str]](null=False, default=dict)
    is_early_startup = models.BooleanField(null=False, default=False)
    has_remote_schema = models.BooleanField(null=False, default=False)

    objects = NimbusVersionedSchemaManager()

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
    experiment_data = models.JSONField[dict[str, Any]](
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
        RESULTS_UPDATED = "Experiment results updated"
        EXPIRED_FROM_PREVIEW = "Expired from preview collection after 30 days"
        REMOVED_FROM_PREVIEW = "Removed from preview collection"
        PUSHED_TO_PREVIEW = "Pushed to preview collection"

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
