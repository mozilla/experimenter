import decimal
import json

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.forms.models import ModelChoiceIterator
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from experimenter.base.models import Country, Locale
from experimenter.bugzilla import get_bugzilla_id
from experimenter.experiments import tasks
from experimenter.experiments.changelog_utils import generate_change_log
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.models import Experiment, ExperimentComment
from experimenter.experiments.serializers.entities import ChangeLogSerializer
from experimenter.notifications.models import Notification


class JSONField(forms.CharField):

    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            try:
                json.loads(cleaned_value)
            except json.JSONDecodeError:
                raise forms.ValidationError("This is not valid JSON.")

        return cleaned_value


class BugzillaURLField(forms.URLField):

    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            err_str = "Please Provide a Valid URL ex: {}show_bug.cgi?id=1234"
            if (
                settings.BUGZILLA_HOST not in cleaned_value
                or get_bugzilla_id(cleaned_value) is None
            ):
                raise forms.ValidationError(err_str.format(settings.BUGZILLA_HOST))

        return cleaned_value


class ChangeLogMixin(object):

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.old_serialized_vals = ChangeLogSerializer(self.instance).data
        else:
            self.old_serialized_vals = None

    def get_changelog_message(self):
        return ""

    def save(self, *args, **kwargs):

        experiment = super().save(*args, **kwargs)
        new_serialized_vals = ChangeLogSerializer(self.instance).data
        message = self.get_changelog_message()
        generate_change_log(
            self.old_serialized_vals,
            new_serialized_vals,
            experiment,
            self.changed_data,
            self.request.user,
            message,
            self.fields,
        )
        return experiment


class ExperimentOverviewForm(ChangeLogMixin, forms.ModelForm):

    type = forms.ChoiceField(
        label="Type", choices=Experiment.TYPE_CHOICES, help_text=Experiment.TYPE_HELP_TEXT
    )
    owner = forms.ModelChoiceField(
        required=True,
        label="Delivery Owner",
        help_text=Experiment.OWNER_HELP_TEXT,
        queryset=get_user_model().objects.all().order_by("email"),
        # This one forces the <select> widget to not include a blank
        # option which would otherwise be included because the model field
        # is nullable.
        empty_label=None,
    )
    name = forms.CharField(label="Name", help_text=Experiment.NAME_HELP_TEXT)
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    short_description = forms.CharField(
        label="Description",
        help_text=Experiment.SHORT_DESCRIPTION_HELP_TEXT,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    public_name = forms.CharField(
        required=False, label="Public Name", help_text=Experiment.PUBLIC_NAME_HELP_TEXT
    )
    public_description = forms.CharField(
        required=False,
        label="Public Description",
        help_text=Experiment.PUBLIC_DESCRIPTION_HELP_TEXT,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    data_science_bugzilla_url = BugzillaURLField(
        required=False,
        label="Data Science Bugzilla URL",
        help_text=Experiment.DATA_SCIENCE_BUGZILLA_HELP_TEXT,
    )
    engineering_owner = forms.CharField(
        required=False,
        label="Engineering Owner",
        help_text=Experiment.ENGINEERING_OWNER_HELP_TEXT,
    )
    analysis_owner = forms.ModelChoiceField(
        required=False,
        label="Data Science Owner",
        help_text=Experiment.ANALYSIS_OWNER_HELP_TEXT,
        queryset=get_user_model().objects.all().order_by("email"),
        # This one forces the <select> widget to not include a blank
        # option which would otherwise be included because the model field
        # is nullable.
        empty_label="Data Science Owner",
    )
    feature_bugzilla_url = BugzillaURLField(
        required=False,
        label="Feature Bugzilla URL",
        help_text=Experiment.FEATURE_BUGZILLA_HELP_TEXT,
    )
    related_work = forms.CharField(
        required=False,
        label="Related Work URLs",
        help_text=Experiment.RELATED_WORK_HELP_TEXT,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    related_to = forms.ModelMultipleChoiceField(
        label="Related Deliveries",
        required=False,
        help_text="Is this related to a previously run delivery?",
        queryset=Experiment.objects.all(),
    )

    class Meta:
        model = Experiment
        fields = [
            "type",
            "owner",
            "name",
            "slug",
            "short_description",
            "public_name",
            "public_description",
            "data_science_bugzilla_url",
            "analysis_owner",
            "engineering_owner",
            "feature_bugzilla_url",
            "related_work",
            "related_to",
        ]

    related_to.widget.attrs.update({"data-live-search": "true"})

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)

        if not slug:
            raise forms.ValidationError(
                "This name must include non-punctuation characters."
            )

        if (
            self.instance.pk is None
            and slug
            and self.Meta.model.objects.filter(slug=slug).exists()
        ):
            raise forms.ValidationError("This name is already in use.")

        return name

    def clean(self):
        cleaned_data = super().clean()

        if self.instance.slug:
            del cleaned_data["slug"]
        else:
            name = cleaned_data.get("name")
            cleaned_data["slug"] = slugify(name)

        if cleaned_data["type"] != ExperimentConstants.TYPE_ROLLOUT:
            required_msg = "This field is required."
            required_fields = (
                "data_science_bugzilla_url",
                "public_name",
                "public_description",
            )
            for required_field in required_fields:
                if (
                    not cleaned_data.get(required_field)
                    and required_field not in self._errors
                ):
                    self._errors[required_field] = [required_msg]

        return cleaned_data


class CustomModelChoiceIterator(ModelChoiceIterator):

    def __iter__(self):
        yield (CustomModelMultipleChoiceField.ALL_KEY, self.field.all_label)
        for choice in super().__iter__():
            yield choice


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Return a ModelMultipleChoiceField but with the exception that
    there's one extra "All" choice inserted as the first choice.
    And when submitted, if "All" was one of the choices, reset
    it to chose nothing."""

    ALL_KEY = "__all__"

    def __init__(self, *args, **kwargs):
        self.all_label = kwargs.pop("all_label")
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if value is not None:
            if self.ALL_KEY in value:
                value = []
            return super().clean(value)

    iterator = CustomModelChoiceIterator


class ExperimentTimelinePopulationForm(ChangeLogMixin, forms.ModelForm):
    proposed_start_date = forms.DateField(
        required=False,
        label="Proposed Start Date",
        help_text=Experiment.PROPOSED_START_DATE_HELP_TEXT,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    proposed_duration = forms.IntegerField(
        required=False,
        min_value=1,
        label="Proposed Total Duration (days)",
        help_text=Experiment.PROPOSED_DURATION_HELP_TEXT,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    proposed_enrollment = forms.IntegerField(
        required=False,
        min_value=1,
        label="Proposed Enrollment Duration (days)",
        help_text=Experiment.PROPOSED_ENROLLMENT_HELP_TEXT,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    rollout_playbook = forms.ChoiceField(
        required=False,
        label="Rollout Playbook",
        choices=Experiment.ROLLOUT_PLAYBOOK_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text=Experiment.ROLLOUT_PLAYBOOK_HELP_TEXT,
    )
    population_percent = forms.DecimalField(
        required=False,
        label="Population Percentage",
        help_text=Experiment.POPULATION_PERCENT_HELP_TEXT,
        initial="0.00",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    firefox_min_version = forms.ChoiceField(
        required=False,
        choices=Experiment.MIN_VERSION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text=Experiment.VERSION_HELP_TEXT,
    )
    firefox_max_version = forms.ChoiceField(
        required=False,
        choices=Experiment.MAX_VERSION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    firefox_channel = forms.ChoiceField(
        required=False,
        choices=Experiment.CHANNEL_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Firefox Channel",
        help_text=Experiment.CHANNEL_HELP_TEXT,
    )
    locales = CustomModelMultipleChoiceField(
        required=False,
        label="Locales",
        all_label="All locales",
        help_text="Applicable only if you don't select All",
        queryset=Locale.objects.all(),
        to_field_name="code",
    )
    countries = CustomModelMultipleChoiceField(
        required=False,
        label="Countries",
        all_label="All countries",
        help_text="Applicable only if you don't select All",
        queryset=Country.objects.all(),
        to_field_name="code",
    )
    platform = forms.ChoiceField(
        required=False,
        label="Platform",
        help_text=Experiment.PLATFORM_HELP_TEXT,
        choices=Experiment.PLATFORM_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    client_matching = forms.CharField(
        required=False,
        label="Population Filtering",
        help_text=Experiment.CLIENT_MATCHING_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 10}),
    )
    # See https://developer.snapappointments.com/bootstrap-select/examples/
    # for more options that relate to the initial rendering of the HTML
    # as a way to customize how it works.
    locales.widget.attrs.update({"data-live-search": "true"})
    countries.widget.attrs.update({"data-live-search": "true"})

    class Meta:
        model = Experiment
        fields = [
            "proposed_start_date",
            "proposed_duration",
            "proposed_enrollment",
            "rollout_playbook",
            "population_percent",
            "firefox_min_version",
            "firefox_max_version",
            "firefox_channel",
            "locales",
            "countries",
            "platform",
            "client_matching",
        ]

    def __init__(self, *args, **kwargs):
        data = kwargs.pop("data", None)
        instance = kwargs.pop("instance", None)
        if instance:
            # The reason we must do this is because the form fields
            # for locales and countries don't know about the instance
            # not having anything set, and we want the "All" option to
            # appear in the generated HTML widget.
            kwargs.setdefault("initial", {})
            if not instance.locales.all().exists():
                kwargs["initial"]["locales"] = [CustomModelMultipleChoiceField.ALL_KEY]
            if not instance.countries.all().exists():
                kwargs["initial"]["countries"] = [CustomModelMultipleChoiceField.ALL_KEY]
        super().__init__(data=data, instance=instance, *args, **kwargs)

    def clean_population_percent(self):
        population_percent = self.cleaned_data.get("population_percent")

        if population_percent and not (0 < population_percent <= 100):
            raise forms.ValidationError(
                "The population size must be between 0 and 100 percent."
            )

        return population_percent

    def clean_firefox_max_version(self):
        firefox_min_version = self.cleaned_data.get("firefox_min_version")
        firefox_max_version = self.cleaned_data.get("firefox_max_version")

        if firefox_min_version and firefox_max_version:
            if firefox_max_version < firefox_min_version:
                raise forms.ValidationError(
                    "The max version must be larger than or equal to the min version."
                )

            return firefox_max_version

    def clean_proposed_start_date(self):
        start_date = self.cleaned_data.get("proposed_start_date")

        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError(
                "The delivery start date must be no earlier than the current date."
            )

        return start_date

    def clean(self):
        cleaned_data = super().clean()

        # enrollment may be None
        enrollment = cleaned_data.get("proposed_enrollment")
        duration = cleaned_data.get("proposed_duration")

        if (enrollment and duration) and enrollment > duration:
            msg = (
                "Enrollment duration is optional, but if set, "
                "must be lower than the delivery duration. "
                "If enrollment duration is not specified - users "
                "are enrolled for the entire delivery."
            )
            self._errors["proposed_enrollment"] = [msg]

        return cleaned_data

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if self.instance.is_rollout:
            rollout_size = self.instance.rollout_dates.get(
                "first_increase"
            ) or self.instance.rollout_dates.get("final_increase")

            if rollout_size:
                experiment.population_percent = decimal.Decimal(rollout_size["percent"])
                experiment.save()

        return experiment


class RadioWidget(forms.widgets.RadioSelect):
    template_name = "experiments/radio_widget.html"


class RadioWidgetCloser(forms.widgets.RadioSelect):
    """
        This radio widget is similar to the RadioWidget
        except for the No and Yes buttons are closer together.
    """

    template_name = "experiments/radio_widget_closer.html"


class ExperimentObjectivesForm(ChangeLogMixin, forms.ModelForm):
    RADIO_OPTIONS = ((False, "No"), (True, "Yes"))

    def coerce_truthy(value):
        if type(value) == bool:
            return value
        if value.lower() == "true":
            return True
        return False

    objectives = forms.CharField(
        required=False,
        label="Objectives",
        help_text=Experiment.OBJECTIVES_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )

    analysis = forms.CharField(
        required=False,
        label="Analysis Plan",
        help_text=Experiment.ANALYSIS_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )

    survey_required = forms.TypedChoiceField(
        required=False,
        label=Experiment.SURVEY_REQUIRED_LABEL,
        help_text=Experiment.SURVEY_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidgetCloser,
        coerce=coerce_truthy,
        empty_value=None,
    )
    survey_urls = forms.CharField(
        required=False,
        help_text=Experiment.SURVEY_HELP_TEXT,
        label="Survey URLs",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 1}),
    )
    survey_instructions = forms.CharField(
        required=False,
        label=Experiment.SURVEY_INSTRUCTIONS_LABEL,
        help_text=Experiment.SURVEY_LAUNCH_INSTRUCTIONS_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 10}),
    )

    class Meta:
        model = Experiment
        fields = (
            "objectives",
            "analysis",
            "survey_required",
            "survey_urls",
            "survey_instructions",
        )


class ExperimentResultsForm(ChangeLogMixin, forms.ModelForm):
    results_url = forms.URLField(
        label="Primary Results URL",
        help_text=Experiment.RESULTS_URL_HELP_TEXT,
        required=False,
    )
    results_initial = forms.CharField(
        label="Initial Results",
        help_text=Experiment.RESULTS_INITIAL_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 10}),
        required=False,
    )
    results_lessons_learned = forms.CharField(
        label="Lessons Learned",
        help_text=Experiment.RESULTS_LESSONS_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
        required=False,
    )

    class Meta:
        model = Experiment
        fields = ("results_url", "results_initial", "results_lessons_learned")


class ExperimentRisksForm(ChangeLogMixin, forms.ModelForm):
    RADIO_OPTIONS = ((False, "No"), (True, "Yes"))

    def coerce_truthy(value):
        if type(value) == bool:
            return value
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False

    # Radio Buttons
    risk_partner_related = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_PARTNER_RELATED_LABEL,
        help_text=Experiment.RISK_PARTNER_RELATED_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_brand = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_BRAND_LABEL,
        help_text=Experiment.RISK_BRAND_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_fast_shipped = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_FAST_SHIPPED_LABEL,
        help_text=Experiment.RISK_FAST_SHIPPED_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_confidential = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_CONFIDENTIAL_LABEL,
        help_text=Experiment.RISK_CONFIDENTIAL_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_release_population = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_RELEASE_POPULATION_LABEL,
        help_text=Experiment.RISK_RELEASE_POPULATION_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_revenue = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_REVENUE_LABEL,
        help_text=Experiment.RISK_REVENUE_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_data_category = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_DATA_CATEGORY_LABEL,
        help_text=Experiment.RISK_DATA_CATEGORY_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_external_team_impact = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_EXTERNAL_TEAM_IMPACT_LABEL,
        help_text=Experiment.RISK_EXTERNAL_TEAM_IMPACT_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_telemetry_data = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_TELEMETRY_DATA_LABEL,
        help_text=Experiment.RISK_TELEMETRY_DATA_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_ux = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_UX_LABEL,
        help_text=Experiment.RISK_UX_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_security = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_SECURITY_LABEL,
        help_text=Experiment.RISK_SECURITY_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_revision = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_REVISION_LABEL,
        help_text=Experiment.RISK_REVISION_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_technical = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_TECHNICAL_LABEL,
        help_text=Experiment.RISK_TECHNICAL_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )
    risk_higher_risk = forms.TypedChoiceField(
        required=False,
        label=Experiment.RISK_HIGHER_RISK_LABEL,
        help_text=Experiment.RISK_HIGHER_RISK_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
        coerce=coerce_truthy,
        empty_value=None,
    )

    # Optional Risk Descriptions
    risk_technical_description = forms.CharField(
        required=False,
        label="Technical Risks Description",
        help_text=Experiment.RISK_TECHNICAL_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": Experiment.RISK_TECHNICAL_DEFAULT,
            }
        ),
    )
    risks = forms.CharField(
        required=False,
        label="Risks",
        help_text=Experiment.RISKS_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 20,
                "placeholder": Experiment.RISKS_DEFAULT,
            }
        ),
    )

    # Testing
    testing = forms.CharField(
        required=False,
        label="Test Instructions",
        help_text=Experiment.TESTING_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": Experiment.TESTING_DEFAULT,
            }
        ),
    )
    test_builds = forms.CharField(
        required=False,
        label="Test Builds",
        help_text=Experiment.TEST_BUILDS_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": Experiment.TEST_BUILDS_DEFAULT,
            }
        ),
    )
    qa_status = forms.CharField(
        required=False,
        label="QA Status",
        help_text=Experiment.QA_STATUS_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": Experiment.QA_STATUS_DEFAULT,
            }
        ),
    )

    class Meta:
        model = Experiment
        fields = (
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
            "risk_technical_description",
            "risks",
            "testing",
            "test_builds",
            "qa_status",
        )


class ExperimentReviewForm(ExperimentConstants, ChangeLogMixin, forms.ModelForm):
    # Required
    review_science = forms.BooleanField(
        required=False,
        label="Data Science Sign-Off",
        help_text=Experiment.REVIEW_SCIENCE_HELP_TEXT,
    )
    review_engineering = forms.BooleanField(
        required=False,
        label="Engineering Allocated",
        help_text=Experiment.REVIEW_ENGINEERING_HELP_TEXT,
    )
    review_qa_requested = forms.BooleanField(
        required=False,
        label=mark_safe(
            f"QA <a href={settings.JIRA_URL} target='_blank'>" "Jira</a> Request Sent"
        ),
        help_text=Experiment.REVIEW_QA_REQUESTED_HELP_TEXT,
    )
    review_intent_to_ship = forms.BooleanField(
        required=False,
        label="Intent to Ship Email Sent",
        help_text=Experiment.REVIEW_INTENT_TO_SHIP_HELP_TEXT,
    )
    review_bugzilla = forms.BooleanField(
        required=False,
        label="Bugzilla Updated",
        help_text=Experiment.REVIEW_BUGZILLA_HELP_TEXT,
    )
    review_qa = forms.BooleanField(
        required=False, label="QA Sign-Off", help_text=Experiment.REVIEW_QA_HELP_TEXT
    )
    review_relman = forms.BooleanField(
        required=False,
        label="Release Management Sign-Off",
        help_text=Experiment.REVIEW_RELMAN_HELP_TEXT,
    )

    # Optional
    review_advisory = forms.BooleanField(
        required=False,
        label="Lightning Advisory",
        help_text=Experiment.REVIEW_LIGHTNING_ADVISING_HELP_TEXT,
    )
    review_legal = forms.BooleanField(
        required=False,
        label="Legal Review",
        help_text=Experiment.REVIEW_GENERAL_HELP_TEXT,
    )
    review_ux = forms.BooleanField(
        required=False, label="UX Review", help_text=Experiment.REVIEW_GENERAL_HELP_TEXT
    )
    review_security = forms.BooleanField(
        required=False,
        label="Security Review",
        help_text=Experiment.REVIEW_GENERAL_HELP_TEXT,
    )
    review_vp = forms.BooleanField(
        required=False, label="VP Sign Off", help_text=Experiment.REVIEW_GENERAL_HELP_TEXT
    )
    review_data_steward = forms.BooleanField(
        required=False,
        label="Data Steward Review",
        help_text=Experiment.REVIEW_GENERAL_HELP_TEXT,
    )
    review_comms = forms.BooleanField(
        required=False,
        label="Mozilla Press/Comms",
        help_text=Experiment.REVIEW_GENERAL_HELP_TEXT,
    )
    review_impacted_teams = forms.BooleanField(
        required=False,
        label="Review from a Fx Module Peer",
        help_text=Experiment.REVIEW_GENERAL_HELP_TEXT,
    )

    class Meta:
        model = Experiment
        fields = (
            # Required
            "review_science",
            "review_engineering",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_bugzilla",
            "review_qa",
            "review_relman",
            # Optional
            "review_advisory",
            "review_legal",
            "review_ux",
            "review_security",
            "review_vp",
            "review_data_steward",
            "review_comms",
            "review_impacted_teams",
        )

    @property
    def required_reviews(self):
        return [self[r] for r in self.instance.get_all_required_reviews()]

    @property
    def optional_reviews(self):
        reviews = set(self.fields) - set(self.instance.get_all_required_reviews())

        if self.instance.is_rollout:
            reviews -= set(["review_science", "review_bugzilla", "review_engineering"])

        return [self[r] for r in sorted(reviews)]

    @property
    def added_reviews(self):
        return [
            strip_tags(self.fields[field_name].label)
            for field_name in self.changed_data
            if self.cleaned_data[field_name]
        ]

    @property
    def removed_reviews(self):
        return [
            strip_tags(self.fields[field_name].label)
            for field_name in self.changed_data
            if not self.cleaned_data[field_name]
        ]

    def get_changelog_message(self):
        message = ""

        if self.added_reviews:
            message += "Added sign-offs: {reviews} ".format(
                reviews=", ".join(self.added_reviews)
            )

        if self.removed_reviews:
            message += "Removed sign-offs: {reviews} ".format(
                reviews=", ".join(self.removed_reviews)
            )

        return message

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if self.changed_data:
            Notification.objects.create(
                user=self.request.user, message=self.get_changelog_message()
            )

        return experiment

    def clean(self):

        super(ExperimentReviewForm, self).clean()

        permissions = [
            (
                "review_qa",
                "experiments.can_check_QA_signoff",
                "You don't have permission to edit QA signoff fields",
            ),
            (
                "review_relman",
                "experiments.can_check_relman_signoff",
                "You don't have permission to edit Release " "Management signoff fields",
            ),
        ]

        # user cannot check or uncheck QA and relman
        # sign off boxes without permission
        for field_name, permission_name, error_message in permissions:
            if field_name in self.changed_data and not self.request.user.has_perm(
                permission_name
            ):
                self.changed_data.remove(field_name)
                self.cleaned_data.pop(field_name)
                messages.warning(self.request, error_message)

        return self.cleaned_data


class ExperimentStatusForm(ExperimentConstants, ChangeLogMixin, forms.ModelForm):

    attention = forms.CharField(required=False)

    class Meta:
        model = Experiment
        fields = ("status", "attention")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_status = self.instance.status

    @property
    def new_status(self):
        return self.cleaned_data["status"]

    def clean_status(self):
        expected_status = self.new_status in self.STATUS_TRANSITIONS[self.old_status]

        if self.old_status != self.new_status and not expected_status:
            raise forms.ValidationError(
                (
                    "You can not change a Delivery's status "
                    "from {old_status} to {new_status}"
                ).format(old_status=self.old_status, new_status=self.new_status)
            )

        return self.new_status

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if (
            self.old_status == Experiment.STATUS_DRAFT
            and self.new_status == Experiment.STATUS_REVIEW
            and not experiment.bugzilla_id
        ):

            tasks.create_experiment_bug_task.delay(self.request.user.id, experiment.id)
            tasks.update_exp_id_to_ds_bug_task.delay(self.request.user.id, experiment.id)

        if (
            self.old_status == Experiment.STATUS_REVIEW
            and self.new_status == Experiment.STATUS_SHIP
            and experiment.bugzilla_id
            and experiment.should_use_normandy
        ):
            experiment.normandy_slug = experiment.generate_normandy_slug()
            experiment.save()

            tasks.update_experiment_bug_task.delay(self.request.user.id, experiment.id)

            tasks.update_ds_bug_task.delay(experiment.id)

        return experiment


class ExperimentArchiveForm(ExperimentConstants, ChangeLogMixin, forms.ModelForm):

    archived = forms.BooleanField(required=False)

    class Meta:
        model = Experiment
        fields = ("archived",)

    def clean_archived(self):
        return not self.instance.archived

    def get_changelog_message(self):
        message = "Archived Delivery"
        if not self.instance.archived:
            message = "Unarchived Delivery"
        return message

    def save(self, *args, **kwargs):
        experiment = Experiment.objects.get(id=self.instance.id)

        if not experiment.is_archivable:
            notification_msg = "This delivery cannot be archived in its current state!"
            Notification.objects.create(user=self.request.user, message=notification_msg)
            return experiment

        experiment = super().save(*args, **kwargs)
        tasks.update_bug_resolution_task.delay(self.request.user.id, experiment.id)
        return experiment


class ExperimentSubscribedForm(ExperimentConstants, forms.ModelForm):

    subscribed = forms.BooleanField(required=False)

    class Meta:
        model = Experiment
        fields = ()

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.initial["subscribed"] = self.instance.subscribers.filter(
            id=self.request.user.id
        ).exists()

    def clean_subscribed(self):
        return self.instance.subscribers.filter(id=self.request.user.id).exists()

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if self.cleaned_data["subscribed"]:
            experiment.subscribers.remove(self.request.user)
        else:
            experiment.subscribers.add(self.request.user)

        return experiment


class ExperimentCommentForm(forms.ModelForm):
    created_by = forms.CharField(required=False)
    text = forms.CharField(required=True)
    section = forms.ChoiceField(required=True, choices=Experiment.SECTION_CHOICES)

    class Meta:
        model = ExperimentComment
        fields = ("experiment", "section", "created_by", "text")

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_created_by(self):
        return self.request.user


class NormandyIdForm(ChangeLogMixin, forms.ModelForm):

    IDS_ADDED_MESSAGE = "Recipe ID(s) Added"

    normandy_id = forms.IntegerField(
        label="Primary Recipe ID",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Primary Recipe ID"}
        ),
    )

    other_normandy_ids = forms.CharField(
        label="Other Recipe IDs",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Other Recipe IDs (Optional)"}
        ),
        required=False,
    )

    def get_changelog_message(self):
        return self.IDS_ADDED_MESSAGE

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("normandy_id") in cleaned_data.get("other_normandy_ids", []):
            raise forms.ValidationError(
                {"other_normandy_ids": "Duplicate IDs are not accepted."}
            )

        return cleaned_data

    def clean_other_normandy_ids(self):
        if not self.cleaned_data["other_normandy_ids"].strip():
            return []

        try:
            return [
                int(i.strip()) for i in self.cleaned_data["other_normandy_ids"].split(",")
            ]
        except ValueError:
            raise forms.ValidationError(f"IDs must be numbers separated by commas.")

    class Meta:
        model = Experiment
        fields = ("normandy_id", "other_normandy_ids")


class ExperimentOrderingForm(forms.Form):
    ORDERING_CHOICES = (
        ("-latest_change", "Most Recently Updated"),
        ("latest_change", "Least Recently Updated"),
        ("firefox_min_version", "Firefox Min Version Ascending"),
        ("-firefox_min_version", "Firefox Min Version Descending"),
        ("firefox_channel_sort", "Firefox Channel Ascending"),
        ("-firefox_channel_sort", "Firefox Channel Descending"),
    )

    ordering = forms.ChoiceField(
        choices=ORDERING_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
