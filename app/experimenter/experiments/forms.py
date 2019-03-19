import json

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.forms import BaseInlineFormSet
from django.forms import inlineformset_factory
from django.forms.models import ModelChoiceIterator
from django.utils import timezone

from experimenter.base.models import Country, Locale
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments import tasks
from experimenter.experiments.models import (
    Experiment,
    ExperimentComment,
    ExperimentChangeLog,
    ExperimentVariant,
)
from experimenter.notifications.models import Notification
from experimenter.projects.forms import (
    NameSlugFormMixin,
    UniqueNameSlugFormMixin,
)


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
    BUGZILLA_BASE_URL = "https://bugzilla.mozilla.org/"

    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            if self.BUGZILLA_BASE_URL not in cleaned_value:
                raise forms.ValidationError(
                    "Please provide a valid Bugzilla URL"
                )

        return cleaned_value


class ChangeLogMixin(object):

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def get_changelog_message(self):
        return ""

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        old_status = None

        latest_change = experiment.changes.latest()
        if latest_change:
            old_status = latest_change.new_status

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            changed_by=self.request.user,
            old_status=old_status,
            new_status=experiment.status,
            message=self.get_changelog_message(),
        )

        return experiment


class ExperimentOverviewForm(
    UniqueNameSlugFormMixin, ChangeLogMixin, forms.ModelForm
):

    type = forms.ChoiceField(
        label="Type",
        choices=Experiment.TYPE_CHOICES,
        help_text=Experiment.TYPE_HELP_TEXT,
    )
    owner = forms.ModelChoiceField(
        required=True,
        label="Experiment Owner",
        help_text=Experiment.OWNER_HELP_TEXT,
        queryset=get_user_model().objects.all().order_by("email"),
        # This one forces the <select> widget to not include a blank
        # option which would otherwise be included because the model field
        # is nullable.
        empty_label=None,
    )
    engineering_owner = forms.CharField(
        required=False,
        label="Engineering Owner",
        help_text=Experiment.ENGINEERING_OWNER_HELP_TEXT,
    )
    name = forms.CharField(label="Name", help_text=Experiment.NAME_HELP_TEXT)
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    short_description = forms.CharField(
        label="Short Description",
        help_text=Experiment.SHORT_DESCRIPTION_HELP_TEXT,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    data_science_bugzilla_url = BugzillaURLField(
        label="Data Science Bugzilla URL",
        help_text=Experiment.DATA_SCIENCE_BUGZILLA_HELP_TEXT,
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
    proposed_start_date = forms.DateField(
        label="Proposed Start Date",
        help_text=Experiment.PROPOSED_START_DATE_HELP_TEXT,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )
    proposed_duration = forms.IntegerField(
        min_value=1,
        label="Proposed Experiment Duration (days)",
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

    class Meta:
        model = Experiment
        fields = [
            "type",
            "owner",
            "engineering_owner",
            "name",
            "slug",
            "short_description",
            "data_science_bugzilla_url",
            "feature_bugzilla_url",
            "related_work",
            "proposed_start_date",
            "proposed_duration",
            "proposed_enrollment",
        ]

    def clean_proposed_start_date(self):
        start_date = self.cleaned_data["proposed_start_date"]

        if start_date < timezone.now().date():
            raise forms.ValidationError(
                (
                    "The experiment start date must "
                    "be no earlier than the current date."
                )
            )

        return start_date

    def clean(self):
        cleaned_data = super().clean()

        # enrollment may be None
        enrollment = cleaned_data.get("proposed_enrollment", 0) or 0

        if enrollment > cleaned_data.get("proposed_duration", 0):
            msg = (
                "The enrollment duration must be less than "
                "or equal to the experiment duration."
            )
            self._errors["proposed_enrollment"] = [msg]

        return cleaned_data


class ExperimentVariantAddonForm(NameSlugFormMixin, forms.ModelForm):

    experiment = forms.ModelChoiceField(
        queryset=Experiment.objects.all(), required=False
    )
    is_control = forms.BooleanField(required=False)
    ratio = forms.IntegerField(
        label="Branch Size",
        initial="50",
        help_text=Experiment.CONTROL_RATIO_HELP_TEXT,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    name = forms.CharField(
        label="Name",
        help_text=Experiment.CONTROL_NAME_HELP_TEXT,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    description = forms.CharField(
        label="Description",
        help_text=Experiment.CONTROL_DESCRIPTION_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    slug = forms.CharField(required=False)

    class Meta:
        model = ExperimentVariant
        fields = [
            "description",
            "experiment",
            "is_control",
            "name",
            "ratio",
            "slug",
        ]


class ExperimentVariantPrefForm(ExperimentVariantAddonForm):

    value = JSONField(
        label="Pref Value",
        help_text=Experiment.CONTROL_VALUE_HELP_TEXT,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = ExperimentVariant
        fields = [
            "description",
            "experiment",
            "is_control",
            "name",
            "ratio",
            "slug",
            "value",
        ]


class ExperimentVariantsFormSet(BaseInlineFormSet):

    def clean(self):
        alive_forms = [
            form for form in self.forms if not form.cleaned_data["DELETE"]
        ]

        total_percentage = sum(
            [form.cleaned_data.get("ratio", 0) for form in alive_forms]
        )

        if total_percentage != 100:
            for form in alive_forms:
                form._errors["ratio"] = [
                    "The size of all branches must add up to 100"
                ]

        unique_slugs = set([form.cleaned_data["slug"] for form in alive_forms])

        if not len(unique_slugs) == len(alive_forms):
            for form in alive_forms:
                form._errors["name"] = ["All branches must have a unique name"]


class ExperimentVariantsPrefFormSet(ExperimentVariantsFormSet):

    def clean(self):
        super().clean()

        alive_forms = [
            form
            for form in self.forms
            if form.is_valid() and not form.cleaned_data["DELETE"]
        ]

        forms_by_value = {}
        for form in alive_forms:
            value = form.cleaned_data["value"]
            forms_by_value.setdefault(value, []).append(form)

        for dupe_forms in forms_by_value.values():
            if len(dupe_forms) > 1:
                for form in dupe_forms:
                    form.add_error(
                        "value", "All branches must have a unique pref value"
                    )


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


class ExperimentVariantsBaseForm(ChangeLogMixin, forms.ModelForm):

    population_percent = forms.DecimalField(
        label="Population Size",
        help_text=Experiment.POPULATION_PERCENT_HELP_TEXT,
        initial="0.00",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    firefox_version = forms.ChoiceField(
        choices=Experiment.VERSION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    firefox_channel = forms.ChoiceField(
        choices=Experiment.CHANNEL_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    client_matching = forms.CharField(
        label="Population Filtering",
        help_text=Experiment.CLIENT_MATCHING_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 10}),
    )
    locales = CustomModelMultipleChoiceField(
        label="Locales",
        required=False,
        all_label="All locales",
        help_text="Applicable only if you don't select All",
        queryset=Locale.objects.all(),
        to_field_name="code",
    )
    countries = CustomModelMultipleChoiceField(
        label="Countries",
        required=False,
        all_label="All countries",
        help_text="Applicable only if you don't select All",
        queryset=Country.objects.all(),
        to_field_name="code",
    )
    # See https://developer.snapappointments.com/bootstrap-select/examples/
    # for more options that relate to the initial rendering of the HTML
    # as a way to customize how it works.
    locales.widget.attrs.update({"data-live-search": "true"})
    countries.widget.attrs.update({"data-live-search": "true"})

    class Meta:
        model = Experiment
        fields = [
            "population_percent",
            "firefox_version",
            "firefox_channel",
            "client_matching",
            "locales",
            "countries",
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
                kwargs["initial"]["locales"] = [
                    CustomModelMultipleChoiceField.ALL_KEY
                ]
            if not instance.countries.all().exists():
                kwargs["initial"]["countries"] = [
                    CustomModelMultipleChoiceField.ALL_KEY
                ]
        super().__init__(data=data, instance=instance, *args, **kwargs)

        extra = 0
        if instance and instance.variants.count() == 0:
            extra = 2

        FormSet = inlineformset_factory(
            can_delete=True,
            extra=extra,
            form=self.FORMSET_FORM_CLASS,
            formset=self.FORMSET_CLASS,
            model=ExperimentVariant,
            parent_model=Experiment,
        )

        self.variants_formset = FormSet(data=data, instance=instance)

    def clean_population_percent(self):
        population_percent = self.cleaned_data["population_percent"]

        if not (0 < population_percent <= 100):
            raise forms.ValidationError(
                "The population size must be between 0 and 100 percent."
            )

        return population_percent

    def is_valid(self):
        return super().is_valid() and self.variants_formset.is_valid()

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.variants_formset.save()
        return super().save(*args, **kwargs)


class ExperimentVariantsAddonForm(ExperimentVariantsBaseForm):

    FORMSET_FORM_CLASS = ExperimentVariantAddonForm
    FORMSET_CLASS = ExperimentVariantsFormSet

    addon_name = forms.CharField(
        required=False,
        label="Add-on Name",
        help_text=Experiment.ADDON_NAME_HELP_TEXT,
    )
    addon_experiment_id = forms.CharField(
        required=False,
        label="Active Experiment Name",
        help_text=Experiment.ADDON_EXPERIMENT_ID_HELP_TEXT,
    )
    addon_testing_url = forms.URLField(
        required=False,
        label="Signed Testing URL",
        help_text=Experiment.ADDON_TESTING_URL_HELP_TEXT,
    )
    addon_release_url = forms.URLField(
        required=False,
        label="Signed Release URL",
        help_text=Experiment.ADDON_RELEASE_URL_HELP_TEXT,
    )

    class Meta:
        model = Experiment
        fields = ExperimentVariantsBaseForm.Meta.fields + [
            "addon_name",
            "addon_experiment_id",
            "addon_testing_url",
            "addon_release_url",
        ]


class ExperimentVariantsPrefForm(ExperimentVariantsBaseForm):

    FORMSET_FORM_CLASS = ExperimentVariantPrefForm
    FORMSET_CLASS = ExperimentVariantsPrefFormSet

    pref_key = forms.CharField(
        label="Pref Name",
        help_text=Experiment.PREF_KEY_HELP_TEXT,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    pref_type = forms.ChoiceField(
        label="Pref Type",
        help_text=Experiment.PREF_TYPE_HELP_TEXT,
        choices=Experiment.PREF_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    pref_branch = forms.ChoiceField(
        label="Pref Branch",
        help_text=Experiment.PREF_BRANCH_HELP_TEXT,
        choices=Experiment.PREF_BRANCH_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Experiment
        fields = ExperimentVariantsBaseForm.Meta.fields + [
            "pref_key",
            "pref_type",
            "pref_branch",
        ]

    def clean(self):
        cleaned_data = super().clean()

        # Check that each pref value matches the global pref type of the form.
        pref_type = cleaned_data["pref_type"]
        expected_type = {
            Experiment.PREF_TYPE_BOOL: bool,
            Experiment.PREF_TYPE_INT: int,
            Experiment.PREF_TYPE_STR: str,
        }[pref_type]

        for form in self.variants_formset.forms:
            if not form.is_valid():
                # This probably means that JSONField got invalid JSON.
                continue
            # Form field is string, but we check value type of parsed JSON.
            found_type = type(json.loads(form.cleaned_data["value"]))
            if found_type != expected_type:
                form.add_error(
                    "value", f"Unexpected value type (should be {pref_type})"
                )

        return cleaned_data


class ExperimentObjectivesForm(ChangeLogMixin, forms.ModelForm):

    objectives = forms.CharField(
        label="Objectives",
        help_text=Experiment.OBJECTIVES_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )
    analysis_owner = forms.CharField(
        label="Data Science Owner",
        help_text=Experiment.ANALYSIS_OWNER_HELP_TEXT,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    analysis = forms.CharField(
        label="Analysis Plan",
        help_text=Experiment.ANALYSIS_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )

    class Meta:
        model = Experiment
        fields = ("objectives", "analysis_owner", "analysis")


class RadioWidget(forms.widgets.RadioSelect):
    template_name = "experiments/radio_widget.html"


class ExperimentRisksForm(ChangeLogMixin, forms.ModelForm):
    RADIO_OPTIONS = ((False, "No"), (True, "Yes"))

    # Radio Buttons
    risk_partner_related = forms.ChoiceField(
        label=Experiment.RISK_PARTNER_RELATED_LABEL,
        help_text=Experiment.RISK_PARTNER_RELATED_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_brand = forms.ChoiceField(
        label=Experiment.RISK_BRAND_LABEL,
        help_text=Experiment.RISK_BRAND_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_fast_shipped = forms.ChoiceField(
        label=Experiment.RISK_FAST_SHIPPED_LABEL,
        help_text=Experiment.RISK_FAST_SHIPPED_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_confidential = forms.ChoiceField(
        label=Experiment.RISK_CONFIDENTIAL_LABEL,
        help_text=Experiment.RISK_CONFIDENTIAL_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_release_population = forms.ChoiceField(
        label=Experiment.RISK_RELEASE_POPULATION_LABEL,
        help_text=Experiment.RISK_RELEASE_POPULATION_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_technical = forms.ChoiceField(
        label=Experiment.RISK_TECHNICAL_LABEL,
        help_text=Experiment.RISK_TECHNICAL_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
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
            "risk_technical",
            "risk_technical_description",
            "risks",
            "testing",
            "test_builds",
            "qa_status",
        )


class ExperimentReviewForm(
    ExperimentConstants, ChangeLogMixin, forms.ModelForm
):
    # Required
    review_science = forms.BooleanField(
        required=False,
        label="Data Science Peer Review",
        help_text=Experiment.REVIEW_SCIENCE_HELP_TEXT,
    )
    review_engineering = forms.BooleanField(
        required=False,
        label="Engineering Allocated",
        help_text=Experiment.REVIEW_ENGINEERING_HELP_TEXT,
    )
    review_qa_requested = forms.BooleanField(
        required=False,
        label="QA Requested",
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
        required=False,
        label="QA Sign-Off",
        help_text=Experiment.REVIEW_QA_HELP_TEXT,
    )
    review_relman = forms.BooleanField(
        required=False,
        label="Release Management Sign-Off",
        help_text=Experiment.REVIEW_RELMAN_HELP_TEXT,
    )

    # Optional
    review_advisory = forms.BooleanField(
        required=False,
        label="Lightning Advisory (Optional)",
        help_text=Experiment.REVIEW_ADVISORY_HELP_TEXT,
    )
    review_legal = forms.BooleanField(
        required=False,
        label="Legal Review (Optional)",
        help_text=Experiment.REVIEW_LEGAL_HELP_TEXT,
    )
    review_ux = forms.BooleanField(
        required=False,
        label="UX Review (Optional)",
        help_text=Experiment.REVIEW_UX_HELP_TEXT,
    )
    review_security = forms.BooleanField(
        required=False,
        label="Security Review (Optional)",
        help_text=Experiment.REVIEW_SECURITY_HELP_TEXT,
    )
    review_vp = forms.BooleanField(
        required=False,
        label="VP Review (Optional)",
        help_text=Experiment.REVIEW_VP_HELP_TEXT,
    )
    review_data_steward = forms.BooleanField(
        required=False,
        label="Data Steward Review (Optional)",
        help_text=Experiment.REVIEW_DATA_STEWARD_HELP_TEXT,
    )
    review_comms = forms.BooleanField(
        required=False,
        label="Mozilla Press/Comms (Optional)",
        help_text=Experiment.REVIEW_COMMS_HELP_TEXT,
    )
    review_impacted_teams = forms.BooleanField(
        required=False,
        label="Impacted Team(s) Signed-Off (Optional)",
        help_text=Experiment.REVIEW_IMPACTED_TEAMS_HELP_TEXT,
    )

    class Meta:
        model = Experiment
        fields = (
            # Required
            "review_science",
            "review_advisory",
            "review_engineering",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_bugzilla",
            "review_qa",
            "review_relman",
            # Optional
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
        return (
            self["review_science"],
            self["review_advisory"],
            self["review_engineering"],
            self["review_qa_requested"],
            self["review_intent_to_ship"],
            self["review_bugzilla"],
            self["review_qa"],
            self["review_relman"],
        )

    @property
    def optional_reviews(self):
        return (
            self["review_legal"],
            self["review_ux"],
            self["review_security"],
            self["review_vp"],
            self["review_data_steward"],
            self["review_comms"],
            self["review_impacted_teams"],
        )

    @property
    def added_reviews(self):
        return [
            self.fields[field_name].label
            for field_name in self.changed_data
            if self.cleaned_data[field_name]
        ]

    @property
    def removed_reviews(self):
        return [
            self.fields[field_name].label
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


class ExperimentStatusForm(
    ExperimentConstants, ChangeLogMixin, forms.ModelForm
):

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
        expected_status = (
            self.new_status in self.STATUS_TRANSITIONS[self.old_status]
        )

        if self.old_status != self.new_status and not expected_status:
            raise forms.ValidationError(
                (
                    "You can not change an Experiment's status "
                    "from {old_status} to {new_status}"
                ).format(
                    old_status=self.old_status, new_status=self.new_status
                )
            )

        return self.new_status

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if (
            self.old_status == Experiment.STATUS_DRAFT
            and self.new_status == Experiment.STATUS_REVIEW
            and not experiment.bugzilla_id
        ):
            needs_attention = len(self.cleaned_data.get("attention", "")) > 0

            tasks.send_review_email_task.delay(
                self.request.user.id,
                experiment.name,
                experiment.experiment_url,
                needs_attention,
            )
            tasks.create_experiment_bug_task.delay(
                self.request.user.id, experiment.id
            )

        if (
            self.old_status == Experiment.STATUS_REVIEW
            and self.new_status == Experiment.STATUS_SHIP
            and experiment.bugzilla_id
        ):
            experiment.normandy_slug = experiment.generate_normandy_slug()
            experiment.save()

            tasks.add_experiment_comment_task.delay(
                self.request.user.id, experiment.id
            )

        return experiment


class ExperimentArchiveForm(
    ExperimentConstants, ChangeLogMixin, forms.ModelForm
):

    archived = forms.BooleanField(required=False)

    class Meta:
        model = Experiment
        fields = ("archived",)

    def clean_archived(self):
        return not self.instance.archived


class ExperimentCommentForm(forms.ModelForm):
    created_by = forms.CharField(required=False)
    text = forms.CharField(required=True)
    section = forms.ChoiceField(
        required=True, choices=Experiment.SECTION_CHOICES
    )

    class Meta:
        model = ExperimentComment
        fields = ("experiment", "section", "created_by", "text")

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_created_by(self):
        return self.request.user
