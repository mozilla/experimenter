import json

from django import forms
from django.contrib.auth import get_user_model
from django.forms import BaseInlineFormSet
from django.forms import inlineformset_factory
from django.utils.text import slugify

from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments import tasks
from experimenter.experiments.models import (
    Experiment,
    ExperimentComment,
    ExperimentChangeLog,
    ExperimentVariant,
)
from experimenter.notifications.models import Notification
from experimenter.projects.forms import AutoNameSlugFormMixin


class JSONField(forms.CharField):

    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            try:
                json.loads(cleaned_value)
            except json.JSONDecodeError:
                raise forms.ValidationError("This is not valid JSON.")

        return cleaned_value


class NameSlugMixin(object):

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        cleaned_data["slug"] = slugify(name)

        return cleaned_data


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
    AutoNameSlugFormMixin, ChangeLogMixin, forms.ModelForm
):

    type = forms.ChoiceField(
        label="Type",
        choices=Experiment.TYPE_CHOICES,
        help_text=Experiment.TYPE_HELP_TEXT,
    )
    owner = forms.ModelChoiceField(
        required=False,
        label="Owner",
        help_text=Experiment.OWNER_HELP_TEXT,
        queryset=get_user_model().objects.all().order_by("email"),
    )
    name = forms.CharField(label="Name", help_text=Experiment.NAME_HELP_TEXT)
    slug = forms.CharField(required=False)
    short_description = forms.CharField(
        label="Short Description",
        help_text=Experiment.SHORT_DESCRIPTION_HELP_TEXT,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    proposed_start_date = forms.DateField(
        label="Proposed Start Date",
        help_text=Experiment.PROPOSED_START_DATE_HELP_TEXT,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )
    proposed_end_date = forms.DateField(
        label="Proposed End Date",
        help_text=Experiment.PROPOSED_END_DATE_HELP_TEXT,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    class Meta:
        model = Experiment
        fields = [
            "type",
            "owner",
            "name",
            "slug",
            "short_description",
            "proposed_start_date",
            "proposed_end_date",
        ]


class ExperimentVariantAddonForm(NameSlugMixin, forms.ModelForm):

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
            [form.cleaned_data["ratio"] for form in alive_forms]
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


class ExperimentVariantsAddonForm(ChangeLogMixin, forms.ModelForm):

    FORMSET_FORM_CLASS = ExperimentVariantAddonForm

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

    class Meta:
        model = Experiment
        fields = [
            "population_percent",
            "firefox_version",
            "firefox_channel",
            "client_matching",
        ]

    def __init__(self, *args, **kwargs):
        data = kwargs.pop("data", None)
        instance = kwargs.pop("instance", None)
        super().__init__(data=data, instance=instance, *args, **kwargs)

        extra = 0
        if instance and instance.variants.count() == 0:
            extra = 2

        FormSet = inlineformset_factory(
            can_delete=True,
            extra=extra,
            form=self.FORMSET_FORM_CLASS,
            formset=ExperimentVariantsFormSet,
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

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        for form in self.variants_formset.forms:
            if form.cleaned_data["DELETE"] and form.cleaned_data["id"]:
                form.instance.delete()
            elif form.is_valid():
                form.instance.experiment = experiment
                form.save(*args, **kwargs)

        return experiment


class ExperimentVariantsPrefForm(ExperimentVariantsAddonForm):

    FORMSET_FORM_CLASS = ExperimentVariantPrefForm

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
        fields = ExperimentVariantsAddonForm.Meta.fields + [
            "pref_key",
            "pref_type",
            "pref_branch",
        ]


class ExperimentObjectivesForm(ChangeLogMixin, forms.ModelForm):

    objectives = forms.CharField(
        label="Objectives",
        help_text=Experiment.OBJECTIVES_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )
    analysis_owner = forms.CharField(
        label="Analysis Owner",
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

    risk_partner_related = forms.ChoiceField(
        label=Experiment.RISK_PARTNER_RELATED_LABEL,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_brand = forms.ChoiceField(
        label=Experiment.RISK_BRAND_LABEL,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_fast_shipped = forms.ChoiceField(
        label=Experiment.RISK_FAST_SHIPPED_LABEL,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_confidential = forms.ChoiceField(
        label=Experiment.RISK_CONFIDENTIAL_LABEL,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_release_population = forms.ChoiceField(
        label=Experiment.RISK_RELEASE_POPULATION_LABEL,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risks = forms.CharField(
        label="Risks",
        help_text=Experiment.RISKS_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )
    testing = forms.CharField(
        label="Test Plan",
        help_text=Experiment.TESTING_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )

    class Meta:
        model = Experiment
        fields = (
            "risk_partner_related",
            "risk_brand",
            "risk_fast_shipped",
            "risk_confidential",
            "risk_release_population",
            "risks",
            "testing",
        )


class ExperimentReviewForm(
    ExperimentConstants, ChangeLogMixin, forms.ModelForm
):
    review_phd = forms.BooleanField(
        required=False,
        label="PHD Review",
        help_text=Experiment.REVIEW_PHD_HELP_TEXT,
    )
    review_science = forms.BooleanField(
        required=False,
        label="Science Review",
        help_text=Experiment.REVIEW_SCIENCE_HELP_TEXT,
    )
    review_peer = forms.BooleanField(
        required=False,
        label="Firefox Peer Review",
        help_text=Experiment.REVIEW_PEER_HELP_TEXT,
    )
    review_relman = forms.BooleanField(
        required=False,
        label="Release Management Review",
        help_text=Experiment.REVIEW_RELMAN_HELP_TEXT,
    )
    review_qa = forms.BooleanField(
        required=False,
        label="QA Review",
        help_text=Experiment.REVIEW_QA_HELP_TEXT,
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

    class Meta:
        model = Experiment
        fields = (
            "review_phd",
            "review_science",
            "review_peer",
            "review_relman",
            "review_qa",
            "review_legal",
            "review_ux",
            "review_security",
            "review_vp",
            "review_data_steward",
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
            message += "Added reviews: {reviews} ".format(
                reviews=", ".join(self.added_reviews)
            )

        if self.removed_reviews:
            message += "Removed reviews: {reviews} ".format(
                reviews=", ".join(self.removed_reviews)
            )

        return message

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if self.changed_data:
            Notification.objects.create(
                user=self.request.user, message=self.get_changelog_message()
            )

        if (
            "review_phd" in self.changed_data
            and experiment.review_phd
            and experiment.bugzilla_id
        ):
            tasks.add_experiment_comment_task.delay(
                self.request.user.id, experiment.id
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

        return experiment


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
