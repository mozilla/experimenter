import copy
import datetime
import json
from collections import defaultdict
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import JSONField, Max
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify

from experimenter.base.models import Country, Locale
from experimenter.experiments.constants import ExperimentConstants
from experimenter.projects.models import Project


def default_all_platforms():
    return ExperimentConstants.PLATFORMS_LIST


class ExperimentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(latest_change=Max("changes__changed_on"))

    def get_prefetched(self):
        return self.get_queryset().prefetch_related(
            "changes__changed_by",
            "changes",
            "comments__created_by",
            "comments",
            "countries",
            "locales",
            "owner",
            "preferences",
            "variants__preferences",
            "variants",
        )


class Experiment(ExperimentConstants, models.Model):
    type = models.CharField(
        max_length=255,
        default=ExperimentConstants.TYPE_PREF,
        choices=ExperimentConstants.TYPE_CHOICES,
    )
    owner = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="owned_experiments",
    )
    analysis_owner = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="analyzed_experiments",
    )
    subscribers = models.ManyToManyField(
        get_user_model(), blank=True, related_name="subscribed_experiments"
    )
    related_to = models.ManyToManyField(
        "legacy_experiments.Experiment", blank=True, related_name="related_by"
    )
    parent = models.ForeignKey(
        "legacy_experiments.Experiment", models.SET_NULL, blank=True, null=True
    )
    status = models.CharField(
        max_length=255,
        default=ExperimentConstants.STATUS_DRAFT,
        choices=ExperimentConstants.STATUS_CHOICES,
    )
    archived = models.BooleanField(default=False)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=255, unique=True, blank=False, null=False)
    public_description = models.TextField(blank=True, null=True)
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

    message_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=ExperimentConstants.MESSAGE_TYPE_CHOICES,
    )
    message_template = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=ExperimentConstants.MESSAGE_TEMPLATE_CHOICES,
    )

    is_multi_pref = models.BooleanField(default=False)
    rollout_type = models.CharField(
        max_length=255,
        choices=ExperimentConstants.ROLLOUT_TYPE_CHOICES,
        default=ExperimentConstants.TYPE_PREF,
    )
    rollout_playbook = models.CharField(
        max_length=255,
        choices=ExperimentConstants.ROLLOUT_PLAYBOOK_CHOICES,
        blank=True,
        null=True,
    )

    addon_experiment_id = models.CharField(
        max_length=255, unique=True, blank=True, null=True
    )
    addon_release_url = models.URLField(max_length=400, blank=True, null=True)
    is_branched_addon = models.BooleanField(default=False)

    pref_name = models.CharField(max_length=255, blank=True, null=True)
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
    pref_value = models.TextField(blank=True, null=True)

    population_percent = models.DecimalField(
        max_digits=7, decimal_places=4, default=0.0, blank=True, null=True
    )
    total_enrolled_clients = models.PositiveIntegerField(blank=True, null=True)
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
    client_matching = models.TextField(
        default=ExperimentConstants.CLIENT_MATCHING_DEFAULT, blank=True, null=True
    )
    locales = models.ManyToManyField(Locale, blank=True)
    countries = models.ManyToManyField(Country, blank=True)
    projects = models.ManyToManyField(Project, blank=True)
    platforms = ArrayField(
        models.CharField(max_length=200),
        blank=True,
        null=True,
        default=default_all_platforms,
    )
    windows_versions = ArrayField(
        models.CharField(max_length=200),
        blank=True,
        null=True,
    )
    profile_age = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PROFILE_AGE_CHOICES,
        blank=True,
        null=True,
        default=ExperimentConstants.PROFILES_ALL,
    )
    design = models.TextField(
        default=ExperimentConstants.DESIGN_DEFAULT, blank=True, null=True
    )
    objectives = models.TextField(
        default=ExperimentConstants.OBJECTIVES_DEFAULT, blank=True, null=True
    )
    analysis = models.TextField(
        default=ExperimentConstants.ANALYSIS_DEFAULT, blank=True, null=True
    )

    survey_required = models.BooleanField(default=False)
    survey_urls = models.TextField(blank=True, null=True)
    survey_instructions = models.TextField(blank=True, null=True)

    engineering_owner = models.CharField(max_length=255, blank=True, null=True)

    bugzilla_id = models.CharField(max_length=255, blank=True, null=True)
    recipe_slug = models.CharField(max_length=255, blank=True, null=True)
    normandy_id = models.PositiveIntegerField(blank=True, null=True)
    other_normandy_ids = ArrayField(models.IntegerField(), blank=True, null=True)

    data_science_issue_url = models.URLField(blank=True, null=True)
    feature_bugzilla_url = models.URLField(blank=True, null=True)

    # Risk fields
    risk_partner_related = models.BooleanField(default=None, blank=True, null=True)
    risk_brand = models.BooleanField(default=None, blank=True, null=True)
    risk_fast_shipped = models.BooleanField(default=None, blank=True, null=True)
    risk_confidential = models.BooleanField(default=None, blank=True, null=True)
    risk_release_population = models.BooleanField(default=None, blank=True, null=True)
    risk_revenue = models.BooleanField(default=None, blank=True, null=True)
    risk_data_category = models.BooleanField(default=None, blank=True, null=True)
    risk_external_team_impact = models.BooleanField(default=None, blank=True, null=True)
    risk_telemetry_data = models.BooleanField(default=None, blank=True, null=True)
    risk_ux = models.BooleanField(default=None, blank=True, null=True)
    risk_security = models.BooleanField(default=None, blank=True, null=True)
    risk_revision = models.BooleanField(default=None, blank=True, null=True)
    risk_technical = models.BooleanField(default=None, blank=True, null=True)
    risk_higher_risk = models.BooleanField(default=None, blank=True, null=True)

    risk_technical_description = models.TextField(blank=True, null=True)
    risks = models.TextField(blank=True, null=True)

    # Testing
    testing = models.TextField(blank=True, null=True)
    test_builds = models.TextField(blank=True, null=True)
    qa_status = models.TextField(blank=True, null=True)

    # Review Fields (sign-offs)
    # Required
    review_science = models.BooleanField(default=None, blank=True, null=True)
    review_engineering = models.BooleanField(default=None, blank=True, null=True)
    review_qa_requested = models.BooleanField(default=None, blank=True, null=True)
    review_intent_to_ship = models.BooleanField(default=None, blank=True, null=True)
    review_bugzilla = models.BooleanField(default=None, blank=True, null=True)
    review_qa = models.BooleanField(default=None, blank=True, null=True)
    review_relman = models.BooleanField(default=None, blank=True, null=True)

    # Optional
    review_advisory = models.BooleanField(default=None, blank=True, null=True)
    review_legal = models.BooleanField(default=None, blank=True, null=True)
    review_ux = models.BooleanField(default=None, blank=True, null=True)
    review_security = models.BooleanField(default=None, blank=True, null=True)
    review_vp = models.BooleanField(default=None, blank=True, null=True)
    review_data_steward = models.BooleanField(default=None, blank=True, null=True)
    review_comms = models.BooleanField(default=None, blank=True, null=True)
    review_impacted_teams = models.BooleanField(default=None, blank=True, null=True)

    is_paused = models.BooleanField(default=False)
    is_high_population = models.BooleanField(default=False)

    # results fields
    results_url = models.URLField(blank=True, null=True)
    results_initial = models.TextField(blank=True, null=True)
    results_lessons_learned = models.TextField(blank=True, null=True)

    results_fail_to_launch = models.BooleanField(default=None, blank=True, null=True)
    results_recipe_errors = models.BooleanField(default=None, blank=True, null=True)
    results_restarts = models.BooleanField(default=None, blank=True, null=True)
    results_low_enrollment = models.BooleanField(default=None, blank=True, null=True)
    results_early_end = models.BooleanField(default=None, blank=True, null=True)
    results_no_usable_data = models.BooleanField(default=None, blank=True, null=True)
    results_failures_notes = models.TextField(blank=True, null=True)

    results_changes_to_firefox = models.BooleanField(default=None, blank=True, null=True)
    results_data_for_hypothesis = models.BooleanField(default=None, blank=True, null=True)
    results_confidence = models.BooleanField(default=None, blank=True, null=True)
    results_measure_impact = models.BooleanField(default=None, blank=True, null=True)
    results_impact_notes = models.TextField(blank=True, null=True)

    objects = ExperimentManager()

    class Meta:
        db_table = "experiments_experiment"
        verbose_name = "Experiment"
        verbose_name_plural = "Experiments"

    def get_absolute_url(self):
        return reverse("experiments-detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return "{type}: {name}".format(type=self.get_type_display(), name=self.name)

    @property
    def experiment_url(self):
        return urljoin(
            "https://{host}".format(host=settings.HOSTNAME), self.get_absolute_url()
        )

    @property
    def bugzilla_url(self):
        if self.bugzilla_id:
            return settings.BUGZILLA_DETAIL_URL.format(id=self.bugzilla_id)

    @property
    def monitoring_dashboard_url(self):
        if self.is_begun and self.recipe_slug:
            start_date = (self.start_date or datetime.date.today()) - datetime.timedelta(
                days=1
            )
            end_date = self.end_date + datetime.timedelta(days=2)

            return settings.MONITORING_URL.format(
                slug=self.recipe_slug,
                from_date=start_date.strftime("%Y-%m-%d"),
                to_date=end_date.strftime("%Y-%m-%d"),
            )

    @property
    def should_use_normandy(self):
        return self.type in (
            self.TYPE_PREF,
            self.TYPE_ADDON,
            self.TYPE_ROLLOUT,
            self.TYPE_MESSAGE,
        )

    def generate_recipe_slug(self):
        if self.is_addon_experiment and not self.use_branched_addon_serializer:
            if not self.addon_experiment_id:
                raise ValueError(
                    (
                        "An Add-on experiment requires an Active "
                        "Experiment Name before it can be sent to Normandy"
                    )
                )
            return self.addon_experiment_id

        error_msg = "The {field} must be set before a Normandy slug can be generated"

        if not self.firefox_min_version:
            raise ValueError(error_msg.format(field="Firefox version"))

        if not self.firefox_channel:
            raise ValueError(error_msg.format(field="Firefox channel"))

        if not self.bugzilla_id:
            raise ValueError(error_msg.format(field="Bugzilla ID"))

        version_string = self.firefox_min_version_integer
        if self.firefox_max_version:
            version_string = (
                f"{self.firefox_min_version_integer}-"
                f"{self.firefox_max_version_integer}"
            )

        slug_prefix = f"bug-{self.bugzilla_id}-{self.type}-"
        slug_postfix = f"-{self.firefox_channel}-{version_string}"
        remaining_chars = settings.RECIPE_SLUG_MAX_LEN - len(slug_prefix + slug_postfix)
        truncated_slug = slugify(self.name[:remaining_chars])
        return f"{slug_prefix}{truncated_slug}{slug_postfix}".lower()

    @property
    def normandy_recipe_json(self):
        from experimenter.normandy.serializers import ExperimentRecipeSerializer

        return json.dumps(ExperimentRecipeSerializer(self).data, indent=2)

    @property
    def has_normandy_info(self):
        return self.recipe_slug or self.normandy_id

    @property
    def format_ndt_normandy_urls(self):
        # returns a list of dictionaries containing D.C. and Normandy
        # urls for the main normandy id and other normandy ids if they exist
        normandy_recipe_url = settings.NORMANDY_API_RECIPE_URL
        ndt_recipe_url = settings.NORMANDY_DEVTOOLS_RECIPE_URL
        urls = []

        if self.normandy_id:
            urls.append(
                {
                    "id": self.normandy_id,
                    "normandy_url": normandy_recipe_url.format(id=self.normandy_id),
                    "ndt_url": ndt_recipe_url.format(id=self.normandy_id),
                }
            )

            if self.other_normandy_ids:
                for norm_id in self.other_normandy_ids:
                    urls.append(
                        {
                            "id": norm_id,
                            "normandy_url": normandy_recipe_url.format(id=norm_id),
                            "ndt_url": ndt_recipe_url.format(id=norm_id),
                        }
                    )

        return urls

    @property
    def normandy_devtools_import_url(self):
        return settings.NORMANDY_DEVTOOLS_RECIPE_IMPORT_URL.format(slug=self.slug)

    @property
    def api_recipe_url(self):
        return reverse("experiments-api-recipe", kwargs={"slug": self.slug})

    @property
    def has_external_urls(self):
        return (
            self.bugzilla_url
            or self.monitoring_dashboard_url
            or self.data_science_issue_url
            or self.feature_bugzilla_url
        )

    def _transition_date(self, old_status, new_status):
        for change in self.changes.all():
            if change.old_status == old_status and change.new_status == new_status:
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
        return self._transition_date(
            self.STATUS_LIVE, self.STATUS_COMPLETE
        ) or self._compute_end_date(self.proposed_duration)

    @property
    def total_duration(self):
        return (self.end_date - self.start_date).days

    @property
    def enrollment_ending_soon(self):
        return (self.enrollment_end_date - datetime.date.today()) <= datetime.timedelta(
            days=5
        )

    @property
    def ending_soon(self):
        return (self.end_date - datetime.date.today()) <= datetime.timedelta(days=5)

    @property
    def enrollment_end_date(self):
        changes = self.changes.filter(message="Enrollment Complete")
        if changes:
            return changes[0].changed_on.date()
        if self.proposed_enrollment:
            return self._compute_end_date(self.proposed_enrollment)

    @property
    def enrollment_duration(self):
        return (self.enrollment_end_date - self.start_date).days

    @property
    def observation_duration(self):
        if self.enrollment_end_date:
            duration = (self.end_date - self.enrollment_end_date).days
            return duration
        return 0

    def _format_date(self, date):
        return date.strftime("%b %d, %Y")

    def _format_date_string(self, start_date, end_date):
        start_text = "Unknown"
        if start_date:
            start_text = self._format_date(start_date)

        end_text = "Unknown"
        if end_date:
            end_text = self._format_date(end_date)

        day_text = "days"
        duration_text = "Unknown"
        if start_date and end_date:
            duration = (end_date - start_date).days
            duration_text = str(duration)

            if duration == 1:
                day_text = "day"

        return "{start} - {end} ({duration} {days})".format(
            start=start_text, end=end_text, duration=duration_text, days=day_text
        )

    @property
    def dates(self):
        return self._format_date_string(self.start_date, self.end_date)

    @property
    def enrollment_dates(self):
        return self._format_date_string(self.start_date, self.enrollment_end_date)

    @property
    def observation_dates(self):
        return self._format_date_string(self.enrollment_end_date, self.end_date)

    @property
    def rollout_dates(self):
        if self.start_date and self.end_date:
            dates = {}

            start_date = self._format_date(self.start_date)
            first_increase = self._format_date(
                self.start_date + datetime.timedelta(days=7)
            )
            final_increase = self._format_date(
                self.start_date + datetime.timedelta(days=21)
            )

            if self.rollout_playbook == self.ROLLOUT_PLAYBOOK_LOW_RISK:
                dates["first_increase"] = {"date": start_date, "percent": "25"}
                dates["second_increase"] = {"date": first_increase, "percent": "75"}
                dates["final_increase"] = {"date": final_increase, "percent": "100"}
            elif self.rollout_playbook == self.ROLLOUT_PLAYBOOK_HIGH_RISK:
                dates["first_increase"] = {"date": start_date, "percent": "25"}
                dates["second_increase"] = {"date": first_increase, "percent": "50"}
                dates["final_increase"] = {"date": final_increase, "percent": "100"}
            elif self.rollout_playbook == self.ROLLOUT_PLAYBOOK_MARKETING:
                dates["final_increase"] = {"date": start_date, "percent": "100"}

            return dates

    @cached_property
    def control(self):
        return self.variants.get(is_control=True)

    @property
    def grouped_changes(self):
        grouped_changes = defaultdict(lambda: defaultdict(set))

        for change in self.changes.all():
            grouped_changes[change.changed_on.date()][change.changed_by].add(change)

        return grouped_changes

    @property
    def ordered_changes(self):
        date_ordered_changes = []
        for date, users in sorted(self.grouped_changes.items(), reverse=True):

            date_changes = []
            for user, user_changes in users.items():
                date_changes.append((user, set([c for c in list(user_changes)])))

            date_ordered_changes.append((date, date_changes))

        return date_ordered_changes

    @property
    def is_generic_experiment(self):
        return self.type == self.TYPE_GENERIC

    @property
    def is_addon_experiment(self):
        return self.type == self.TYPE_ADDON

    @property
    def is_pref_experiment(self):
        return self.type == self.TYPE_PREF

    @property
    def is_message_experiment(self):
        return self.type == self.TYPE_MESSAGE

    @property
    def is_rollout(self):
        return self.type == self.TYPE_ROLLOUT

    @property
    def is_pref_rollout(self):
        return self.is_rollout and self.rollout_type == self.TYPE_PREF

    @property
    def is_addon_rollout(self):
        return self.is_rollout and self.rollout_type == self.TYPE_ADDON

    @property
    def is_editable(self):
        return self.status in (self.STATUS_DRAFT, self.STATUS_REVIEW)

    @property
    def is_begun(self):
        return self.status in (self.STATUS_LIVE, self.STATUS_COMPLETE)

    @property
    def is_high_risk(self):
        return any(self._risk_values)

    @property
    def should_have_variants(self):
        return self.type in (
            self.TYPE_PREF,
            self.TYPE_ADDON,
            self.TYPE_GENERIC,
            self.TYPE_MESSAGE,
        )

    @property
    def should_have_population_percent(self):
        return (
            self.type
            in (self.TYPE_PREF, self.TYPE_ADDON, self.TYPE_GENERIC, self.TYPE_MESSAGE)
        ) or (self.is_rollout and self.is_begun)

    @property
    def should_have_total_enrolled(self):
        return self.type not in (self.TYPE_GENERIC, self.TYPE_ROLLOUT)

    @property
    def should_have_telemetry_event(self):
        return self.type == self.TYPE_MESSAGE

    @property
    def display_platforms_or_versions(self):
        if self.windows_versions:
            return ", ".join(self.windows_versions)
        else:
            if set(ExperimentConstants.PLATFORMS_LIST) == set(self.platforms):
                return ExperimentConstants.PLATFORM_ALL

            return ", ".join(self.platforms)

    @property
    def completed_overview(self):
        return self.pk is not None

    @property
    def completed_timeline(self):
        completed = self.proposed_start_date and self.proposed_duration

        if self.is_rollout:
            completed = completed and self.rollout_playbook

        return completed

    @property
    def completed_population(self):
        completed = (
            self.firefox_min_version and self.firefox_max_version and self.firefox_channel
        )

        if self.should_have_population_percent:
            completed = completed and self.population_percent

        return completed

    @property
    def completed_design(self):
        return self.design and self.design != self.DESIGN_DEFAULT

    @property
    def completed_pref_rollout(self):

        return self.is_pref_rollout and self.preferences.count() > 0

    @property
    def completed_addon_rollout(self):
        return self.is_addon_rollout and self.addon_release_url

    @property
    def completed_rollout(self):
        return self.completed_pref_rollout or self.completed_addon_rollout

    @property
    def completed_addon(self):
        if self.is_branched_addon:
            return all([v.addon_release_url for v in self.variants.all()])
        else:
            return self.addon_release_url

    @property
    def completed_variants(self):
        return self.should_have_variants and self.variants.exists()

    @property
    def completed_objectives(self):
        return (
            self.objectives
            and self.objectives != self.OBJECTIVES_DEFAULT
            and self.analysis
            and self.analysis != self.ANALYSIS_DEFAULT
        )

    @property
    def completed_results(self):
        results_fields = (
            "results_url",
            "results_initial",
            "results_lessons_learned",
            "results_fail_to_launch",
            "results_recipe_errors",
            "results_restarts",
            "results_low_enrollment",
            "results_early_end",
            "results_no_usable_data",
            "results_failures_notes",
            "results_changes_to_firefox",
            "results_data_for_hypothesis",
            "results_confidence",
            "results_measure_impact",
            "results_impact_notes",
        )

        return any([getattr(self, field) for field in results_fields])

    @property
    def additional_results(self):
        return any(
            [
                self.results_fail_to_launch,
                self.results_restarts,
                self.results_low_enrollment,
                self.results_early_end,
                self.results_no_usable_data,
                self.results_changes_to_firefox,
                self.results_data_for_hypothesis,
                self.results_measure_impact,
                self.results_impact_notes,
            ]
        )

    @property
    def risk_fields(self):
        risk_fields = (
            "risk_partner_related",
            "risk_brand",
            "risk_fast_shipped",
            "risk_confidential",
            "risk_release_population",
            "risk_revenue",
            "risk_data_category",
            "risk_external_team_impact",
            "risk_telemetry_data",
            "risk_ux",
            "risk_security",
            "risk_revision",
            "risk_technical",
            "risk_higher_risk",
        )

        exclusions = ExperimentConstants.RISK_EXCLUSIONS.get(self.type, [])
        return sorted(list(set(risk_fields) - set(exclusions)))

    @property
    def _risk_values(self):
        return [getattr(self, risk) for risk in self.risk_fields]

    @property
    def risk_values_labels(self):
        return [
            (getattr(self, risk), self.RISK_LABELS[risk]) for risk in self.risk_fields
        ]

    @property
    def completed_risks(self):
        completed = None not in self._risk_values

        if self.risk_technical:
            completed = completed and self.risk_technical_description

        return completed

    @property
    def should_show_risks(self):
        return self.completed_risks or self.is_begun

    @property
    def should_have_test_instructions(self):
        return self.type in [
            self.TYPE_PREF,
            self.TYPE_ADDON,
            self.TYPE_GENERIC,
            self.TYPE_MESSAGE,
        ]

    @property
    def should_have_test_builds(self):
        return self.type in [self.TYPE_PREF, self.TYPE_ADDON, self.TYPE_GENERIC]

    @property
    def completed_testing(self):
        return self.qa_status

    @property
    def _conditional_required_reviews_mapping(self):
        return {
            "review_vp": any(
                (
                    self.risk_partner_related,
                    self.risk_brand,
                    self.risk_fast_shipped,
                    self.risk_confidential,
                    self.risk_release_population,
                    self.risk_revenue,
                )
            ),
            "review_legal": any((self.risk_partner_related, self.risk_data_category)),
            "review_impacted_teams": self.risk_external_team_impact,
            "review_data_steward": self.risk_telemetry_data,
            "review_ux": self.risk_ux,
            "review_security": self.risk_security,
        }

    def _default_required_reviews(self):
        return list(self.SIGNOFF_TYPE_DEFAULTS.get(self.type, self.SIGNOFF_DEFAULTS))

    def get_all_required_reviews(self):
        required_reviews = self._default_required_reviews()
        for review, risk in self._conditional_required_reviews_mapping.items():
            if risk:
                required_reviews.append(review)

        return required_reviews

    @property
    def completed_required_reviews(self):
        required_reviews = self.get_all_required_reviews()

        if not self.is_rollout and "review_advisory" in required_reviews:
            # review advisory is an exception that is not required
            required_reviews.remove("review_advisory")

        return all([getattr(self, r) for r in required_reviews])

    @property
    def completed_all_sections(self):
        completed = (
            self.completed_timeline
            and self.completed_population
            and self.completed_objectives
            and self.completed_risks
        )

        if self.should_have_variants:
            completed = completed and self.completed_variants

        if self.is_addon_experiment:
            completed = completed and self.completed_addon

        if self.is_generic_experiment:
            completed = completed and self.completed_design

        return completed

    @property
    def should_have_signoffs_to_launch(self):
        return self.type not in [self.TYPE_MESSAGE]

    @property
    def is_ready_to_launch(self):
        ready_to_launch = self.completed_all_sections

        if self.should_have_signoffs_to_launch:
            ready_to_launch = ready_to_launch and self.completed_required_reviews

        return ready_to_launch

    @property
    def format_firefox_versions(self):
        if self.firefox_max_version:
            return f"{self.firefox_min_version} to {self.firefox_max_version}"
        else:
            return self.firefox_min_version

    @property
    def firefox_max_version_integer(self):
        if self.firefox_max_version:
            return int(
                ExperimentConstants.VERSION_REGEX.match(self.firefox_max_version).group(0)
            )

    @property
    def firefox_min_version_integer(self):
        return int(
            ExperimentConstants.VERSION_REGEX.match(self.firefox_min_version).group(0)
        )

    @property
    def use_branched_addon_serializer(self):
        return (
            self.is_addon_experiment
            and self.firefox_min_version_integer
            >= ExperimentConstants.FX_MIN_MULTI_BRANCHED_VERSION
        )

    @property
    def use_multi_pref_serializer(self):
        return self.is_pref_experiment and (
            self.firefox_min_version_integer
            >= ExperimentConstants.FX_MIN_MULTI_BRANCHED_VERSION
            or self.is_multi_pref
        )

    @property
    def versions_integer_list(self):
        max = self.firefox_max_version_integer or self.firefox_min_version_integer
        return list(range(self.firefox_min_version_integer, max + 1))

    @property
    def population(self):
        population = "{channel} Firefox {firefox_version}".format(
            firefox_version=self.format_firefox_versions, channel=self.firefox_channel
        )

        if self.should_have_population_percent:
            population = "{percent:g}% of {population}".format(
                population=population, percent=float(self.population_percent)
            )

        return population

    @property
    def is_archivable(self):
        not_archivable = (self.STATUS_LIVE, self.STATUS_ACCEPTED)
        return self.status not in not_archivable

    @property
    def is_enrollment_complete(self):
        return self.is_paused and self.status == self.STATUS_LIVE

    @property
    def is_pref_value_json_string(self):
        return self.pref_type == ExperimentConstants.PREF_TYPE_JSON_STR

    @property
    def is_shipped(self):
        return self.status in (
            Experiment.STATUS_SHIP,
            Experiment.STATUS_ACCEPTED,
            Experiment.STATUS_LIVE,
            Experiment.STATUS_COMPLETE,
        )

    def clone(self, name, user):

        cloned = copy.copy(self)
        variants = ExperimentVariant.objects.filter(experiment=self)

        set_to_none_fields = [
            "addon_experiment_id",
            "addon_release_url",
            "recipe_slug",
            "normandy_id",
            "other_normandy_ids",
            "bugzilla_id",
            "review_science",
            "review_engineering",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_bugzilla",
            "review_qa",
            "review_relman",
            "review_advisory",
            "review_legal",
            "review_ux",
            "review_security",
            "review_vp",
            "review_data_steward",
            "review_comms",
            "review_impacted_teams",
            "proposed_start_date",
            "results_url",
            "results_initial",
            "results_lessons_learned",
            "results_fail_to_launch",
            "results_recipe_errors",
            "results_restarts",
            "results_low_enrollment",
            "results_early_end",
            "results_no_usable_data",
            "results_failures_notes",
            "results_changes_to_firefox",
            "results_data_for_hypothesis",
            "results_confidence",
            "results_measure_impact",
            "results_impact_notes",
        ]

        cloned.id = None
        cloned.name = name
        cloned.slug = slugify(cloned.name)
        cloned.status = ExperimentConstants.STATUS_DRAFT
        cloned.owner = user
        cloned.parent = self
        cloned.archived = False
        cloned.is_paused = False
        cloned.is_high_population = False

        for field in set_to_none_fields:
            setattr(cloned, field, None)

        cloned.save()

        # for the variants on the old experiment, duplicate each
        # with id=none, set the experiment foreignkey to the new clone
        for variant in variants:
            variant.id = None
            variant.experiment = cloned
            variant.save()

            if self.is_multi_pref:
                original_variant = self.variants.get(slug=variant.slug)
                for preference in original_variant.preferences.all():
                    preference.variant = variant
                    preference.id = None
                    preference.save()

        cloned.projects.set(self.projects.all())

        cloned.related_to.add(self)

        cloned.countries.add(*self.countries.all())
        cloned.locales.add(*self.locales.all())

        ExperimentChangeLog.objects.create(
            experiment=cloned,
            changed_by=get_user_model().objects.get(id=user.id),
            old_status=None,
            new_status=ExperimentConstants.STATUS_DRAFT,
            message=ExperimentChangeLog.STATUS_CLONED,
        )

        return cloned


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
    addon_release_url = models.URLField(max_length=400, blank=True, null=True)
    value = models.TextField(blank=True, null=True)
    message_targeting = models.TextField(blank=True, null=True)
    message_threshold = models.TextField(blank=True, null=True)
    message_triggers = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "experiments_experimentvariant"
        verbose_name = "Experiment Variant"
        verbose_name_plural = "Experiment Variants"
        unique_together = (("slug", "experiment"),)

    def __str__(self):
        return self.name

    @property
    def type(self):
        if self.is_control:
            return "Control"
        else:
            return "Treatment"


class Preference(models.Model):
    pref_name = models.CharField(max_length=255, blank=False, null=False)
    pref_type = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PREF_TYPE_CHOICES,
        blank=False,
        null=False,
    )
    pref_value = models.CharField(max_length=4096, blank=False, null=False)

    class Meta:
        abstract = True

    @property
    def is_json_string_type(self):
        return self.pref_type == ExperimentConstants.PREF_TYPE_JSON_STR


class VariantPreferences(Preference):
    pref_branch = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PREF_BRANCH_CHOICES,
        blank=False,
        null=False,
    )

    variant = models.ForeignKey(
        ExperimentVariant,
        blank=False,
        null=False,
        related_name="preferences",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "experiments_variantpreferences"
        unique_together = (("variant", "pref_name"),)


class RolloutPreference(Preference):
    experiment = models.ForeignKey(
        Experiment,
        blank=False,
        null=False,
        related_name="preferences",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "experiments_rolloutpreference"
        unique_together = (("experiment", "pref_name"),)


class ExperimentChangeLogManager(models.Manager):
    def latest(self):
        return self.all().order_by("-changed_on").first()


class ExperimentChangeLog(models.Model):
    STATUS_NONE_DRAFT = "Created Delivery"
    STATUS_DRAFT_DRAFT = "Edited Delivery"
    STATUS_DRAFT_REVIEW = "Ready for Sign-Off"
    STATUS_REVIEW_DRAFT = "Return to Draft"
    STATUS_REVIEW_REVIEW = "Edited Delivery"
    STATUS_REVIEW_SHIP = "Marked as Ready to Ship"
    STATUS_SHIP_ACCEPTED = "Accepted by Normandy"
    STATUS_SHIP_REVIEW = "Canceled Ready to Ship"
    STATUS_ACCEPTED_LIVE = "Launched Delivery"
    STATUS_LIVE_COMPLETE = "Completed Delivery"
    STATUS_ADDED_RESULTS = "Added Results"
    STATUS_CLONED = "Cloned Delivery"

    PRETTY_STATUS_LABELS = {
        None: {Experiment.STATUS_DRAFT: STATUS_NONE_DRAFT},
        Experiment.STATUS_DRAFT: {
            Experiment.STATUS_DRAFT: STATUS_DRAFT_DRAFT,
            Experiment.STATUS_REVIEW: STATUS_DRAFT_REVIEW,
        },
        Experiment.STATUS_REVIEW: {
            Experiment.STATUS_DRAFT: STATUS_REVIEW_DRAFT,
            Experiment.STATUS_REVIEW: STATUS_REVIEW_REVIEW,
            Experiment.STATUS_SHIP: STATUS_REVIEW_SHIP,
        },
        Experiment.STATUS_SHIP: {
            Experiment.STATUS_REVIEW: STATUS_SHIP_REVIEW,
            Experiment.STATUS_ACCEPTED: STATUS_SHIP_ACCEPTED,
        },
        Experiment.STATUS_ACCEPTED: {
            Experiment.STATUS_ACCEPTED: STATUS_DRAFT_DRAFT,
            Experiment.STATUS_LIVE: STATUS_ACCEPTED_LIVE,
        },
        Experiment.STATUS_LIVE: {
            Experiment.STATUS_COMPLETE: STATUS_LIVE_COMPLETE,
            Experiment.STATUS_LIVE: STATUS_ADDED_RESULTS,
        },
        Experiment.STATUS_COMPLETE: {Experiment.STATUS_COMPLETE: STATUS_ADDED_RESULTS},
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
        max_length=255, blank=True, null=True, choices=Experiment.STATUS_CHOICES
    )
    new_status = models.CharField(
        max_length=255, blank=False, null=False, choices=Experiment.STATUS_CHOICES
    )
    message = models.TextField(blank=True, null=True)

    changed_values = JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    objects = ExperimentChangeLogManager()

    class Meta:
        db_table = "experiments_experimentchangelog"
        verbose_name = "Experiment Change Log"
        verbose_name_plural = "Experiment Change Logs"
        ordering = ("changed_on",)

    def __str__(self):
        if self.message:
            return self.message
        else:
            return self.pretty_status

    @property
    def pretty_status(self):
        return self.PRETTY_STATUS_LABELS.get(self.old_status, {}).get(self.new_status, "")


class ExperimentCommentManager(models.Manager):
    @cached_property
    def sections(self):
        sections = defaultdict(list)

        for comment in self.all():
            sections[comment.section].append(comment)

        return sections


class ExperimentEmail(ExperimentConstants, models.Model):
    experiment = models.ForeignKey(
        Experiment, related_name="emails", on_delete=models.CASCADE
    )
    type = models.CharField(
        max_length=255, blank=False, null=False, choices=Experiment.EMAIL_CHOICES
    )
    sent_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "experiments_experimentemail"


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

    def get_absolute_url(self):
        return f"{self.experiment.experiment_url}#comment{self.id}"

    class Meta:
        db_table = "experiments_experimentcomment"
        verbose_name = "Experiment Comment"
        verbose_name_plural = "Experiment Comments"
        ordering = ("created_on",)

    def __str__(self):  # pragma: no cover
        return "{author} ({date}): {text}".format(
            author=self.created_by, date=self.created_on, text=self.text
        )
