import json
import re

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from experimenter.base.models import Country, Locale
from experimenter.bugzilla import get_bugzilla_id, tasks
from experimenter.experiments.changelog_utils import (
    ChangeLogSerializer,
    generate_change_log,
)
from experimenter.experiments.constants import ExperimentConstants
from experimenter.legacy.legacy_experiments.models import Experiment, ExperimentComment
from experimenter.notifications.models import Notification
from experimenter.projects.models import Project

RADIO_NO = False
RADIO_YES = True
RADIO_OPTIONS = ((RADIO_NO, "No"), (RADIO_YES, "Yes"))


class JSONField(forms.CharField):
    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            try:
                json.loads(cleaned_value)
            except json.JSONDecodeError:
                raise forms.ValidationError("This is not valid JSON.")

        return cleaned_value


class DSIssueURLField(forms.URLField):
    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            err_str = (
                "Please Provide a Valid URL ex: {ds_url}DS-12345 or {ds_url}DO-12345"
            )

            ds = re.match(
                re.escape(settings.DS_ISSUE_HOST) + r"(DS|DO)-(\w+.*)", cleaned_value
            )

            if ds is None:

                raise forms.ValidationError(err_str.format(ds_url=settings.DS_ISSUE_HOST))
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
        label="Type",
        choices=Experiment.FEATURE_TYPE_CHOICES(),
        help_text=Experiment.TYPE_HELP_TEXT,
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
    name = forms.CharField(
        required=True, label="Public Name", help_text=Experiment.PUBLIC_NAME_HELP_TEXT
    )
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    public_description = forms.CharField(
        required=True,
        label="Public Description",
        help_text=Experiment.PUBLIC_DESCRIPTION_HELP_TEXT,
        max_length=1024,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    short_description = forms.CharField(
        required=True,
        label="Internal Description",
        help_text=Experiment.SHORT_DESCRIPTION_HELP_TEXT,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    data_science_issue_url = DSIssueURLField(
        required=False,
        label="Data Science Issue URL",
        help_text=Experiment.DATA_SCIENCE_ISSUE_HELP_TEXT,
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
    related_to = forms.ModelMultipleChoiceField(
        label="Related Deliveries",
        required=False,
        help_text="Is this related to a previously run delivery?",
        queryset=Experiment.objects.all(),
    )
    projects = forms.ModelMultipleChoiceField(
        required=False,
        label="Projects",
        help_text=(
            """Is this delivery related to a specific project?
         Ask in #ask-experimenter on Slack if you need to add a new project"""
        ),
        queryset=Project.objects.all(),
    )

    class Meta:
        model = Experiment
        fields = [
            "type",
            "owner",
            "name",
            "slug",
            "public_description",
            "short_description",
            "data_science_issue_url",
            "analysis_owner",
            "engineering_owner",
            "feature_bugzilla_url",
            "related_to",
            "projects",
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
                "data_science_issue_url",
                "public_description",
            )
            for required_field in required_fields:
                if (
                    not cleaned_data.get(required_field)
                    and required_field not in self._errors
                ):
                    self._errors[required_field] = [required_msg]

        return cleaned_data

    def save(self, *args, **kwargs):
        created = not self.instance.id
        experiment = super().save(*args, **kwargs)

        if created and experiment.is_message_experiment:
            experiment.locales.add(
                *Locale.objects.filter(code__in=experiment.MESSAGE_DEFAULT_LOCALES)
            )
            experiment.countries.add(
                *Country.objects.filter(code__in=experiment.MESSAGE_DEFAULT_COUNTRIES)
            )

        return experiment


class RadioWidget(forms.widgets.RadioSelect):
    template_name = "experiments/radio_widget.html"


class RadioWidgetCloser(RadioWidget):
    """
    This radio widget is similar to the RadioWidget
    except for the No and Yes buttons are closer together.
    """

    template_name = "experiments/radio_widget_closer.html"


class ExperimentObjectivesForm(ChangeLogMixin, forms.ModelForm):

    objectives = forms.CharField(
        required=False,
        label="Hypothesis",
        help_text=Experiment.OBJECTIVES_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )

    total_enrolled_clients = forms.IntegerField(
        required=False,
        min_value=1,
        label="Estimated Total Enrolled Clients",
        help_text=Experiment.TOTAL_ENROLLED_CLIENTS_HELP_TEXT,
    )

    analysis = forms.CharField(
        required=False,
        label="Analysis Plan",
        help_text=Experiment.ANALYSIS_HELP_TEXT,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 20}),
    )

    survey_required = forms.ChoiceField(
        required=False,
        label=Experiment.SURVEY_REQUIRED_LABEL,
        help_text=Experiment.SURVEY_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidgetCloser,
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
            "total_enrolled_clients",
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

    results_recipe_errors = forms.ChoiceField(
        required=False,
        label=Experiment.RESULTS_RECIPE_ERRORS_LABEL,
        help_text=Experiment.RESULTS_QUESTIONS_HELP,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    results_failures_notes = forms.CharField(
        label=Experiment.RESULTS_NOTES_LABEL,
        help_text="",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 10}),
        required=False,
    )

    results_confidence = forms.ChoiceField(
        required=False,
        label=Experiment.RESULTS_CONFIDENCE_LABEL,
        help_text=Experiment.RESULTS_QUESTIONS_HELP,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )

    class Meta:
        model = Experiment
        fields = (
            "results_url",
            "results_initial",
            "results_lessons_learned",
            "results_recipe_errors",
            "results_failures_notes",
            "results_confidence",
        )


class ExperimentRisksForm(ChangeLogMixin, forms.ModelForm):

    # Radio Buttons
    risk_partner_related = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_PARTNER_RELATED_LABEL,
        help_text=Experiment.RISK_PARTNER_RELATED_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_brand = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_BRAND_LABEL,
        help_text=Experiment.RISK_BRAND_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_fast_shipped = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_FAST_SHIPPED_LABEL,
        help_text=Experiment.RISK_FAST_SHIPPED_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_confidential = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_CONFIDENTIAL_LABEL,
        help_text=Experiment.RISK_CONFIDENTIAL_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_release_population = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_RELEASE_POPULATION_LABEL,
        help_text=Experiment.RISK_RELEASE_POPULATION_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_revenue = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_REVENUE_LABEL,
        help_text=Experiment.RISK_REVENUE_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_data_category = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_DATA_CATEGORY_LABEL,
        help_text=Experiment.RISK_DATA_CATEGORY_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_external_team_impact = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_EXTERNAL_TEAM_IMPACT_LABEL,
        help_text=Experiment.RISK_EXTERNAL_TEAM_IMPACT_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_telemetry_data = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_TELEMETRY_DATA_LABEL,
        help_text=Experiment.RISK_TELEMETRY_DATA_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_ux = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_UX_LABEL,
        help_text=Experiment.RISK_UX_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_security = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_SECURITY_LABEL,
        help_text=Experiment.RISK_SECURITY_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_revision = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_REVISION_LABEL,
        help_text=Experiment.RISK_REVISION_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_technical = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_TECHNICAL_LABEL,
        help_text=Experiment.RISK_TECHNICAL_HELP_TEXT,
        choices=RADIO_OPTIONS,
        widget=RadioWidget,
    )
    risk_higher_risk = forms.ChoiceField(
        required=False,
        label=Experiment.RISK_HIGHER_RISK_LABEL,
        help_text=Experiment.RISK_HIGHER_RISK_HELP_TEXT,
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

    @property
    def risk_fields(self):
        return [self[risk] for risk in self.instance.risk_fields]


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
        label="Lightning Advisory (Optional)",
        help_text=Experiment.REVIEW_LIGHTNING_ADVISING_HELP_TEXT,
    )
    review_legal = forms.BooleanField(
        required=False,
        label="Legal Review",
        help_text=Experiment.REVIEW_GENERAL_HELP_TEXT,
    )
    review_ux = forms.BooleanField(
        required=False,
        label="Copy/UX Review",
        help_text=Experiment.REVIEW_GENERAL_HELP_TEXT,
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
                "legacy_experiments.can_check_QA_signoff",
                "You don't have permission to edit QA signoff fields",
            ),
            (
                "review_relman",
                "legacy_experiments.can_check_relman_signoff",
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

        if (
            self.old_status == Experiment.STATUS_REVIEW
            and self.new_status == Experiment.STATUS_SHIP
            and experiment.bugzilla_id
            and experiment.should_use_normandy
        ):
            experiment.recipe_slug = experiment.generate_recipe_slug()
            experiment.save()

            tasks.update_experiment_bug_task.delay(self.request.user.id, experiment.id)

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
            raise forms.ValidationError("IDs must be numbers separated by commas.")

    class Meta:
        model = Experiment
        fields = ("normandy_id", "other_normandy_ids")


class ExperimentOrderingForm(forms.Form):
    ORDERING_CHOICES = (
        ("-latest_change", "Most Recently Updated"),
        ("latest_change", "Least Recently Updated"),
        ("firefox_min_version", "Firefox Min Version Ascending"),
        ("-firefox_min_version", "Firefox Min Version Descending"),
    )

    ordering = forms.ChoiceField(
        choices=ORDERING_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
