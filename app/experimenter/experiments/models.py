import json
import datetime
import time
from collections import defaultdict
from urllib.parse import urljoin
import copy

from typing import cast, Callable, Optional, List, Dict, Any, Tuple, Set

from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Case, Max, Value, When
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from experimenter.base.models import Country, Locale
from experimenter.experiments.constants import ExperimentConstants

from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder


class ExperimentManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().annotate(latest_change=Max("changes__changed_on"))

    def get_prefetched(self):
        return self.get_queryset().prefetch_related(
            "changes",
            "changes__changed_by",
            "owner",
            "comments",
            "comments__created_by",
            "locales",
            "countries",
        )


class Experiment(ExperimentConstants, models.Model):
    type: models.CharField = models.CharField(
        max_length=255,
        default=ExperimentConstants.TYPE_PREF,
        choices=ExperimentConstants.TYPE_CHOICES,
    )
    owner: models.ForeignKey = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="owned_experiments",
    )
    subscribers: models.ManyToManyField = models.ManyToManyField(
        get_user_model(), blank=True, related_name="subscribed_experiments"
    )
    related_to: models.ManyToManyField = models.ManyToManyField(
        "experiments.Experiment", blank=True, related_name="related_by"
    )
    parent: models.ForeignKey = models.ForeignKey(
        "experiments.Experiment", models.SET_NULL, blank=True, null=True
    )
    status: models.CharField = models.CharField(
        max_length=255,
        default=ExperimentConstants.STATUS_DRAFT,
        choices=ExperimentConstants.STATUS_CHOICES,
    )
    archived: models.BooleanField = models.BooleanField(default=False)
    name: models.CharField = models.CharField(
        max_length=255, unique=True, blank=False, null=False
    )
    slug: models.SlugField = models.SlugField(
        max_length=255, unique=True, blank=False, null=False
    )
    short_description: models.TextField = models.TextField(
        default="", blank=True, null=True
    )
    related_work: models.TextField = models.TextField(default="", blank=True, null=True)

    proposed_start_date: models.DateField = models.DateField(blank=True, null=True)
    proposed_duration: models.PositiveIntegerField = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(ExperimentConstants.MAX_DURATION)],
    )
    proposed_enrollment: models.PositiveIntegerField = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(ExperimentConstants.MAX_DURATION)],
    )

    addon_experiment_id: models.CharField = models.CharField(
        max_length=255, unique=True, blank=True, null=True
    )
    addon_release_url: models.URLField = models.URLField(
        max_length=400, blank=True, null=True
    )

    pref_key: models.CharField = models.CharField(max_length=255, blank=True, null=True)
    pref_type: models.CharField = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PREF_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    pref_branch: models.CharField = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PREF_BRANCH_CHOICES,
        blank=True,
        null=True,
    )

    public_name: models.CharField = models.CharField(
        max_length=255, blank=True, null=True
    )

    public_description: models.TextField = models.TextField(blank=True, null=True)
    population_percent: models.DecimalField = models.DecimalField(
        max_digits=7, decimal_places=4, default=0.0
    )
    firefox_min_version: models.CharField = models.CharField(
        max_length=255, choices=ExperimentConstants.VERSION_CHOICES
    )
    firefox_max_version: models.CharField = models.CharField(
        max_length=255, choices=ExperimentConstants.VERSION_CHOICES, blank=True, null=True
    )
    firefox_channel: models.CharField = models.CharField(
        max_length=255, choices=ExperimentConstants.CHANNEL_CHOICES
    )
    client_matching: models.TextField = models.TextField(
        default=ExperimentConstants.CLIENT_MATCHING_DEFAULT, blank=True
    )
    locales: models.ManyToManyField = models.ManyToManyField(Locale, blank=True)
    countries: models.ManyToManyField = models.ManyToManyField(Country, blank=True)
    platform: models.CharField = models.CharField(
        max_length=255,
        choices=ExperimentConstants.PLATFORM_CHOICES,
        default=ExperimentConstants.PLATFORM_ALL,
    )
    objectives: models.TextField = models.TextField(
        default=ExperimentConstants.OBJECTIVES_DEFAULT, blank=True, null=True
    )
    analysis: models.TextField = models.TextField(
        default=ExperimentConstants.ANALYSIS_DEFAULT, blank=True, null=True
    )
    analysis_owner: models.CharField = models.CharField(
        max_length=255, blank=True, null=True
    )

    survey_required: models.BooleanField = models.BooleanField(default=False)
    survey_urls: models.TextField = models.TextField(blank=True, null=True)
    survey_instructions: models.TextField = models.TextField(blank=True, null=True)

    engineering_owner: models.CharField = models.CharField(
        max_length=255, blank=True, null=True
    )

    bugzilla_id: models.CharField = models.CharField(
        max_length=255, blank=True, null=True
    )
    normandy_slug: models.CharField = models.CharField(
        max_length=255, blank=True, null=True
    )
    normandy_id: models.PositiveIntegerField = models.PositiveIntegerField(
        blank=True, null=True
    )
    other_normandy_ids: ArrayField = ArrayField(
        models.IntegerField(), blank=True, null=True
    )

    data_science_bugzilla_url: models.URLField = models.URLField(blank=True, null=True)
    feature_bugzilla_url: models.URLField = models.URLField(blank=True, null=True)

    # Risk fields
    risk_internal_only: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_partner_related: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_brand: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_fast_shipped: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_confidential: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_release_population: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_revenue: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_data_category: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_external_team_impact: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_telemetry_data: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_ux: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_security: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_revision: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_technical: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    risk_technical_description: models.TextField = models.TextField(blank=True, null=True)

    risks: models.TextField = models.TextField(blank=True, null=True)

    # Testing
    testing: models.TextField = models.TextField(blank=True, null=True)
    test_builds: models.TextField = models.TextField(blank=True, null=True)
    qa_status: models.TextField = models.TextField(blank=True, null=True)

    # Review Fields (sign-offs)
    # Required
    review_science: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_engineering: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_qa_requested: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_intent_to_ship: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_bugzilla: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_qa: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_relman: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )

    # Optional
    review_advisory: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_legal: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_ux: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_security: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_vp: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_data_steward: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_comms: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )
    review_impacted_teams: models.NullBooleanField = models.NullBooleanField(
        default=None, blank=True, null=True
    )

    is_paused: models.BooleanField = models.BooleanField(default=False)

    # results fields
    results_url: models.URLField = models.URLField(blank=True, null=True)
    results_initial: models.TextField = models.TextField(blank=True, null=True)
    results_lessons_learned: models.TextField = models.TextField(blank=True, null=True)

    objects = ExperimentManager()

    class Meta:
        verbose_name = "Experiment"
        verbose_name_plural = "Experiments"

    def get_absolute_url(self) -> str:
        return reverse("experiments-detail", kwargs={"slug": self.slug})

    def __str__(self) -> str:
        return self.full_name

    get_type_display: Callable[["Experiment"], str]

    @property
    def full_name(self) -> str:
        return "{type}: {name}".format(type=self.get_type_display(), name=self.name)

    @property
    def experiment_url(self) -> str:
        return urljoin(
            "https://{host}".format(host=settings.HOSTNAME), self.get_absolute_url()
        )

    @property
    def bugzilla_url(self) -> Optional[str]:
        if self.bugzilla_id:
            return str(settings.BUGZILLA_DETAIL_URL.format(id=self.bugzilla_id))
        return None

    @property
    def monitoring_dashboard_url(self) -> Optional[str]:

        def to_timestamp(date: datetime.date) -> int:
            return int(time.mktime(date.timetuple())) * 1000

        start_date = ""
        end_date = ""

        if self.is_begun and self.normandy_slug and self.start_date:
            start_date = str(to_timestamp(self.start_date - datetime.timedelta(days=1)))

            if self.status == self.STATUS_COMPLETE and self.end_date:
                end_date = str(to_timestamp(self.end_date + datetime.timedelta(days=2)))

            return cast(
                str,
                settings.MONITORING_URL.format(
                    slug=self.normandy_slug, from_date=start_date, to_date=end_date
                ),
            )
        return None

    def generate_normandy_slug(self) -> str:
        if self.is_addon_experiment:
            if not self.addon_experiment_id:
                raise ValueError(
                    (
                        "An Add-on experiment requires an Active "
                        "Experiment Name before it can be sent to Normandy"
                    )
                )
            return str(self.addon_experiment_id)

        error_msg = "The {field} must be set before a Normandy slug can be generated"

        if not self.firefox_min_version:
            raise ValueError(error_msg.format(field="Firefox version"))

        if not self.firefox_channel:
            raise ValueError(error_msg.format(field="Firefox channel"))

        if not self.bugzilla_id:
            raise ValueError(error_msg.format(field="Bugzilla ID"))

        version_string = str(self.firefox_min_version_integer)
        if self.firefox_max_version:
            version_string = (
                f"{self.firefox_min_version_integer}-"
                f"{self.firefox_max_version_integer}"
            )

        slug_prefix = f"{self.type}-"
        slug_postfix = (
            f"-{self.firefox_channel}-{version_string}-" f"bug-{self.bugzilla_id}"
        )
        remaining_chars = settings.NORMANDY_SLUG_MAX_LEN - len(slug_prefix + slug_postfix)
        truncated_slug = slugify(self.name[:remaining_chars])
        return f"{slug_prefix}{truncated_slug}{slug_postfix}".lower()

    @property
    def normandy_recipe_json(self) -> str:
        from experimenter.experiments.serializers import ExperimentRecipeSerializer

        return json.dumps(ExperimentRecipeSerializer(self).data, indent=2)

    @property
    def has_normandy_info(self) -> bool:
        return bool(self.normandy_slug or self.normandy_id)

    @property
    def format_dc_normandy_urls(self) -> List[Dict[str, Any]]:
        # returns a list of dictionaries containing D.C. and Normandy
        # urls for the main normandy id and other normandy ids if they exist
        normandy_recipe_url = settings.NORMANDY_API_RECIPE_URL
        delivery_console_url = settings.DELIVERY_CONSOLE_RECIPE_URL

        urls = []

        if self.normandy_id:
            urls.append(
                {
                    "id": self.normandy_id,
                    "normandy_url": normandy_recipe_url.format(id=self.normandy_id),
                    "DC_url": delivery_console_url.format(id=self.normandy_id),
                }
            )

            if self.other_normandy_ids:
                for norm_id in self.other_normandy_ids:
                    urls.append(
                        {
                            "id": norm_id,
                            "normandy_url": normandy_recipe_url.format(id=norm_id),
                            "DC_url": delivery_console_url.format(id=norm_id),
                        }
                    )

        return urls

    @property
    def delivery_console_experiment_import_url(self) -> str:
        return str(settings.DELIVERY_CONSOLE_EXPERIMENT_IMPORT_URL.format(slug=self.slug))

    @property
    def api_recipe_url(self) -> str:
        return reverse("experiments-api-recipe", kwargs={"slug": self.slug})

    @property
    def has_external_urls(self) -> bool:
        return bool(
            self.bugzilla_url
            or self.monitoring_dashboard_url
            or self.data_science_bugzilla_url
            or self.feature_bugzilla_url
        )

    changes: models.Manager

    def _transition_date(self, old_status, new_status) -> Optional[datetime.date]:
        for change in self.changes.all():
            if change.old_status == old_status and change.new_status == new_status:
                return cast(datetime.date, change.changed_on.date())
        return None

    @property
    def start_date(self) -> Optional[datetime.date]:
        return (
            self._transition_date(self.STATUS_ACCEPTED, self.STATUS_LIVE)
            or self.proposed_start_date
        )

    def _compute_end_date(self, duration) -> Optional[datetime.date]:
        if self.start_date and duration and 0 <= duration <= self.MAX_DURATION:
            return self.start_date + datetime.timedelta(days=duration)
        return None

    @property
    def end_date(self) -> Optional[datetime.date]:
        return self._transition_date(
            self.STATUS_LIVE, self.STATUS_COMPLETE
        ) or self._compute_end_date(self.proposed_duration)

    @property
    def enrollment_ending_soon(self) -> bool:
        if self.enrollment_end_date:
            return (
                self.enrollment_end_date - datetime.date.today()
            ) <= datetime.timedelta(days=5)
        return False  # pragma: no cover

    @property
    def ending_soon(self) -> bool:
        if self.end_date:
            return (self.end_date - datetime.date.today()) <= datetime.timedelta(days=5)
        return False  # pragma: no cover

    @property
    def enrollment_end_date(self) -> Optional[datetime.date]:
        return self._compute_end_date(self.proposed_enrollment)

    @property
    def observation_duration(self) -> int:
        if self.proposed_enrollment:
            return int(self.proposed_duration - self.proposed_enrollment)
        return 0

    def _format_date_string(self, start_date, end_date) -> str:
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
            start=start_text, end=end_text, duration=duration_text, days=day_text
        )

    @property
    def dates(self) -> str:
        return self._format_date_string(self.start_date, self.end_date)

    @property
    def enrollment_dates(self) -> str:
        return self._format_date_string(self.start_date, self.enrollment_end_date)

    @property
    def observation_dates(self) -> str:
        return self._format_date_string(self.enrollment_end_date, self.end_date)

    variants: models.Manager

    @cached_property
    def control(self) -> "ExperimentVariant":
        return cast(ExperimentVariant, self.variants.get(is_control=True))

    @property
    def grouped_changes(self) -> defaultdict:
        grouped_changes: defaultdict = defaultdict(lambda: defaultdict(set))

        for change in self.changes.all():
            grouped_changes[change.changed_on.date()][change.changed_by].add(change)

        return grouped_changes

    @property
    def ordered_changes(self) -> List[Tuple[Any, List[Tuple[Any, Set[Any]]]]]:
        date_ordered_changes = []
        for date, users in sorted(self.grouped_changes.items(), reverse=True):

            date_changes = []
            for user, user_changes in users.items():
                date_changes.append((user, set([c for c in list(user_changes)])))

            date_ordered_changes.append((date, date_changes))

        return date_ordered_changes

    @property
    def is_addon_experiment(self) -> bool:
        return bool(self.type == self.TYPE_ADDON)

    @property
    def is_pref_experiment(self) -> bool:
        return bool(self.type == self.TYPE_PREF)

    @property
    def is_editable(self) -> bool:
        return self.status in (self.STATUS_DRAFT, self.STATUS_REVIEW)

    @property
    def is_begun(self) -> bool:
        return self.status in (self.STATUS_LIVE, self.STATUS_COMPLETE)

    @property
    def is_high_risk(self) -> bool:
        return any(self._risk_questions)

    @property
    def completed_overview(self) -> bool:
        return self.pk is not None

    @property
    def completed_timeline(self) -> bool:
        return bool(self.proposed_start_date and self.proposed_duration)

    @property
    def completed_population(self) -> bool:
        return bool(
            self.population_percent > 0
            and self.firefox_min_version != ""
            and self.firefox_channel != ""
        )

    @property
    def completed_addon(self) -> bool:
        return bool(self.addon_experiment_id and self.addon_release_url)

    @property
    def completed_variants(self) -> bool:
        return self.variants.exists()

    @property
    def completed_objectives(self) -> bool:
        return bool(
            self.objectives != self.OBJECTIVES_DEFAULT
            and self.analysis != self.ANALYSIS_DEFAULT
        )

    @property
    def completed_results(self) -> bool:
        return bool(
            self.results_url or self.results_initial or self.results_lessons_learned
        )

    @property
    def _risk_questions(self) -> Tuple:
        return (
            self.risk_internal_only,
            self.risk_partner_related,
            self.risk_brand,
            self.risk_fast_shipped,
            self.risk_confidential,
            self.risk_release_population,
            self.risk_revenue,
            self.risk_data_category,
            self.risk_external_team_impact,
            self.risk_telemetry_data,
            self.risk_ux,
            self.risk_security,
            self.risk_revision,
            self.risk_technical,
        )

    @property
    def completed_risks(self) -> bool:
        return None not in self._risk_questions

    @property
    def completed_testing(self) -> bool:
        return bool(self.qa_status)

    @property
    def _conditional_required_reviews_mapping(self) -> Dict[str, bool]:
        return {
            "review_vp": any(
                [
                    self.risk_partner_related,
                    self.risk_brand,
                    self.risk_fast_shipped,
                    self.risk_confidential,
                    self.risk_release_population,
                    self.risk_revenue,
                ]
            ),
            "review_legal": any([self.risk_partner_related, self.risk_data_category]),
            "review_impacted_teams": self.risk_external_team_impact,
            "review_data_steward": self.risk_telemetry_data,
            "review_ux": self.risk_ux,
            "review_security": self.risk_security,
        }

    def _default_required_reviews(self) -> List[str]:
        return [
            "review_science",
            "review_advisory",
            "review_engineering",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_bugzilla",
            "review_qa",
            "review_relman",
        ]

    def get_all_required_reviews(self) -> List[str]:
        required_reviews = self._default_required_reviews()
        for review, risk in self._conditional_required_reviews_mapping.items():
            if risk:
                required_reviews.append(review)
        return required_reviews

    @property
    def completed_required_reviews(self) -> bool:
        required_reviews = self.get_all_required_reviews()

        # review advisory is an exception that is not required
        required_reviews.remove("review_advisory")
        return all([getattr(self, r) for r in required_reviews])

    @property
    def completed_all_sections(self) -> bool:
        completed = (
            self.completed_timeline
            and self.completed_population
            and self.completed_variants
            and self.completed_objectives
            and self.completed_risks
        )

        if self.is_addon_experiment:
            completed = completed and self.completed_addon

        return completed

    @property
    def is_ready_to_launch(self) -> bool:
        return self.completed_all_sections and self.completed_required_reviews

    @property
    def format_firefox_versions(self) -> str:
        if self.firefox_max_version:
            return f"{self.firefox_min_version} to {self.firefox_max_version}"
        else:
            return str(self.firefox_min_version)

    @property
    def firefox_max_version_integer(self) -> Optional[int]:
        if self.firefox_max_version:
            match = ExperimentConstants.VERSION_REGEX.match(self.firefox_max_version)
            if match:
                return int(match.group(0))
        return None

    @property
    def firefox_min_version_integer(self) -> Optional[int]:
        match = ExperimentConstants.VERSION_REGEX.match(self.firefox_min_version)
        if match:
            return int(match.group(0))
        return None  # pragma: no cover

    @property
    def versions_integer_list(self) -> List[int]:
        max = self.firefox_max_version_integer or self.firefox_min_version_integer
        if self.firefox_min_version_integer and max:
            return list(range(self.firefox_min_version_integer, max + 1))
        return []  # pragma: no cover

    @property
    def population(self) -> str:
        return "{percent:g}% of {channel} Firefox {firefox_version}".format(
            percent=float(self.population_percent),
            firefox_version=self.format_firefox_versions,
            channel=self.firefox_channel,
        )

    @staticmethod
    def firefox_channel_sort() -> Case:
        """A Case that can be added to an Experiment QuerySet to sort."""
        return Case(
            When(
                firefox_channel=ExperimentConstants.CHANNEL_RELEASE,
                then=Value(ExperimentConstants.CHANNEL_RELEASE_ORDER),
            ),
            When(
                firefox_channel=ExperimentConstants.CHANNEL_BETA,
                then=Value(ExperimentConstants.CHANNEL_BETA_ORDER),
            ),
            When(
                firefox_channel=ExperimentConstants.CHANNEL_NIGHTLY,
                then=Value(ExperimentConstants.CHANNEL_NIGHTLY_ORDER),
            ),
            default=Value(ExperimentConstants.CHANNEL_UNSET_ORDER),
            output_field=models.IntegerField(),
        )

    @property
    def is_archivable(self) -> bool:
        not_archivable = (self.STATUS_LIVE, self.STATUS_ACCEPTED)
        return self.status not in not_archivable

    @property
    def is_enrollment_complete(self) -> bool:
        return bool(self.is_paused and self.status == self.STATUS_LIVE)

    id: Optional[int]

    def clone(self, name, user) -> "Experiment":

        cloned = copy.copy(self)
        variants = ExperimentVariant.objects.filter(experiment=self)

        set_to_none_fields = [
            "addon_experiment_id",
            "addon_release_url",
            "normandy_slug",
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
        ]

        cloned.id = None
        cloned.name = name
        cloned.slug = slugify(cloned.name)
        cloned.status = ExperimentConstants.STATUS_DRAFT
        cloned.owner = user
        cloned.parent = self
        cloned.archived = False

        for field in set_to_none_fields:
            setattr(cloned, field, None)

        cloned.save()

        # for the variants on the old experiment, duplicate each
        # with id=none, set the experiment foreignkey to the new clone
        for variant in variants:
            variant.id = None
            variant.experiment = cloned
            variant.save()

        ExperimentChangeLog.objects.create(
            experiment=cloned,
            changed_by=get_user_model().objects.get(id=user.id),
            old_status=None,
            new_status=ExperimentConstants.STATUS_DRAFT,
        )

        return cloned


class ExperimentVariant(models.Model):
    experiment: models.ForeignKey = models.ForeignKey(
        Experiment,
        blank=False,
        null=False,
        related_name="variants",
        on_delete=models.CASCADE,
    )
    name: models.CharField = models.CharField(max_length=150, blank=False, null=False)
    slug: models.SlugField = models.SlugField(max_length=255, blank=False, null=False)
    is_control: models.BooleanField = models.BooleanField(default=False)
    description: models.TextField = models.TextField(default="")
    ratio: models.PositiveIntegerField = models.PositiveIntegerField(default=1)
    value: models.TextField = models.TextField(blank=False, null=True)

    class Meta:
        verbose_name = "Experiment Variant"
        verbose_name_plural = "Experiment Variants"
        unique_together = (("slug", "experiment"),)

    def __str__(self) -> str:
        return str(self.name)

    @property
    def type(self) -> str:
        if self.is_control:
            return "Control"
        else:
            return "Treatment"


class ExperimentChangeLogManager(models.Manager):

    def latest(self) -> Optional["ExperimentChangeLog"]:  # type: ignore
        return self.all().order_by("-changed_on").first()


class ExperimentChangeLog(models.Model):
    STATUS_NONE_DRAFT = "Created Experiment"
    STATUS_DRAFT_DRAFT = "Edited Experiment"
    STATUS_DRAFT_REVIEW = "Ready for Sign-Off"
    STATUS_REVIEW_DRAFT = "Return to Draft"
    STATUS_REVIEW_REVIEW = "Edited Experiment"
    STATUS_REVIEW_SHIP = "Marked as Ready to Ship"
    STATUS_SHIP_ACCEPTED = "Accepted by Normandy"
    STATUS_SHIP_REVIEW = "Canceled Ready to Ship"
    STATUS_ACCEPTED_LIVE = "Launched Experiment"
    STATUS_LIVE_COMPLETE = "Completed Experiment"
    STATUS_ADDED_RESULTS = "Added Results"

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
        Experiment.STATUS_ACCEPTED: {Experiment.STATUS_LIVE: STATUS_ACCEPTED_LIVE},
        Experiment.STATUS_LIVE: {
            Experiment.STATUS_COMPLETE: STATUS_LIVE_COMPLETE,
            Experiment.STATUS_LIVE: STATUS_ADDED_RESULTS,
        },
        Experiment.STATUS_COMPLETE: {Experiment.STATUS_COMPLETE: STATUS_ADDED_RESULTS},
    }

    def current_datetime():  # type: ignore
        return timezone.now()

    experiment: models.ForeignKey = models.ForeignKey(
        Experiment,
        blank=False,
        null=False,
        related_name="changes",
        on_delete=models.CASCADE,
    )
    changed_on: models.DateTimeField = models.DateTimeField(default=current_datetime)
    changed_by: models.ForeignKey = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE
    )
    old_status: models.CharField = models.CharField(
        max_length=255, blank=True, null=True, choices=Experiment.STATUS_CHOICES
    )
    new_status: models.CharField = models.CharField(
        max_length=255, blank=False, null=False, choices=Experiment.STATUS_CHOICES
    )
    message: models.TextField = models.TextField(blank=True, null=True)

    old_values = JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    new_values = JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    objects = ExperimentChangeLogManager()

    class Meta:
        verbose_name = "Experiment Change Log"
        verbose_name_plural = "Experiment Change Logs"
        ordering = ("changed_on",)

    def __str__(self) -> str:
        if self.message:
            return str(self.message)
        else:
            return self.pretty_status

    @property
    def changed_values(self) -> Optional[Dict[str, Dict[str, str]]]:

        def _get_code(list_of_obj) -> str:
            return ", ".join([obj["code"] for obj in list_of_obj])

        if self.new_values:
            changed_values = {}
            # ensure change log has new_values
            for key in self.new_values:
                if key in ("countries", "locales"):
                    old_val = _get_code(self.old_values[key])
                    new_val = _get_code(self.new_values[key])
                else:
                    old_val = self.old_values[key]
                    new_val = self.new_values[key]
                changed_values[key] = {"old_value": old_val, "new_value": new_val}
            return changed_values
        return None

    @property
    def pretty_status(self) -> str:
        return self.PRETTY_STATUS_LABELS.get(self.old_status, {}).get(self.new_status, "")


class ExperimentCommentManager(models.Manager):

    @cached_property
    def sections(self) -> defaultdict:
        sections: defaultdict = defaultdict(list)

        for comment in self.all():
            sections[comment.section].append(comment)

        return sections


class ExperimentEmail(ExperimentConstants, models.Model):
    experiment: models.ForeignKey = models.ForeignKey(
        Experiment, related_name="emails", on_delete=models.CASCADE
    )
    type: models.CharField = models.CharField(
        max_length=255, blank=False, null=False, choices=Experiment.EMAIL_CHOICES
    )
    sent_on: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Experiment Email"
        verbose_name_plural = "Experiment Emails"
        ordering = ("sent_on",)


class ExperimentComment(ExperimentConstants, models.Model):
    experiment: models.ForeignKey = models.ForeignKey(
        Experiment, related_name="comments", on_delete=models.CASCADE
    )
    created_by: models.ForeignKey = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE
    )
    created_on: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    section: models.CharField = models.CharField(
        max_length=255, choices=ExperimentConstants.SECTION_CHOICES
    )
    text: models.TextField = models.TextField()

    objects = ExperimentCommentManager()

    class Meta:
        verbose_name = "Experiment Comment"
        verbose_name_plural = "Experiment Comments"
        ordering = ("created_on",)

    def __str__(self) -> str:  # pragma: no cover
        return "{author} ({date}): {text}".format(
            author=self.created_by, date=self.created_on, text=self.text
        )
