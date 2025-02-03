from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.http import HttpRequest
from django.utils.text import slugify

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.models import (
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.nimbus_ui_new.constants import NimbusUIConstants
from experimenter.outcomes import Outcomes
from experimenter.projects.models import Project
from experimenter.segments import Segments
from experimenter.targeting.constants import NimbusTargetingConfig


class NimbusChangeLogFormMixin:
    def __init__(self, *args, request: HttpRequest = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def get_changelog_message(self) -> str:
        raise NotImplementedError

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        generate_nimbus_changelog(
            experiment, self.request.user, self.get_changelog_message()
        )
        return experiment


class NimbusExperimentCreateForm(NimbusChangeLogFormMixin, forms.ModelForm):
    owner = forms.ModelChoiceField(
        User.objects.all(),
        widget=forms.widgets.HiddenInput(),
    )
    name = forms.CharField(
        label="",
        widget=forms.widgets.TextInput(
            attrs={
                "placeholder": "Public Name",
            }
        ),
    )
    slug = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput(),
    )
    hypothesis = forms.CharField(
        label="",
        widget=forms.widgets.Textarea(),
        initial=NimbusUIConstants.HYPOTHESIS_PLACEHOLDER,
    )
    application = forms.ChoiceField(
        label="",
        choices=NimbusExperiment.Application.choices,
        widget=forms.widgets.Select(
            attrs={
                "class": "form-select",
            },
        ),
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "owner",
            "name",
            "slug",
            "hypothesis",
            "application",
        ]

    def get_changelog_message(self):
        return f'{self.request.user} created {self.cleaned_data["name"]}'

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)
        if not slug:
            raise forms.ValidationError(NimbusUIConstants.ERROR_NAME_INVALID)
        if NimbusExperiment.objects.filter(slug=slug).exists():
            raise forms.ValidationError(NimbusUIConstants.ERROR_SLUG_DUPLICATE)
        return name

    def clean_hypothesis(self):
        hypothesis = self.cleaned_data["hypothesis"]
        if hypothesis.strip() == NimbusUIConstants.HYPOTHESIS_PLACEHOLDER.strip():
            raise forms.ValidationError(NimbusUIConstants.ERROR_HYPOTHESIS_PLACEHOLDER)
        return hypothesis

    def clean(self):
        cleaned_data = super().clean()
        if "name" in cleaned_data:
            cleaned_data["slug"] = slugify(cleaned_data["name"])
        return cleaned_data


class QAStatusForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ["qa_status", "qa_comment"]
        widgets = {
            "qa_status": forms.Select(choices=NimbusExperiment.QAStatus),
        }

    def get_changelog_message(self):
        return f"{self.request.user} updated QA"


class TakeawaysForm(NimbusChangeLogFormMixin, forms.ModelForm):
    conclusion_recommendations = forms.MultipleChoiceField(
        choices=NimbusExperiment.ConclusionRecommendation.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "takeaways_metric_gain",
            "takeaways_gain_amount",
            "takeaways_qbr_learning",
            "takeaways_summary",
            "conclusion_recommendations",
        ]

    def get_changelog_message(self):
        return f"{self.request.user} updated takeaways"


class SignoffForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ["qa_signoff", "vp_signoff", "legal_signoff"]
        widgets = {
            "qa_signoff": forms.CheckboxInput(),
            "vp_signoff": forms.CheckboxInput(),
            "legal_signoff": forms.CheckboxInput(),
        }

    def get_changelog_message(self):
        return f"{self.request.user} updated sign off"


class MultiSelectWidget(forms.SelectMultiple):
    class_attrs = "selectpicker form-control"

    def __init__(self, *args, attrs=None, **kwargs):
        attrs = attrs or {}
        attrs.update(
            {
                "class": self.class_attrs,
                "data-live-search": "true",
                "data-live-search-placeholder": "Search",
            }
        )

        super().__init__(*args, attrs=attrs, **kwargs)


class InlineRadioSelect(forms.RadioSelect):
    template_name = "common/widgets/inline_radio.html"
    option_template_name = "common/widgets/inline_radio_option.html"


class NimbusDocumentationLinkForm(forms.ModelForm):
    title = forms.ChoiceField(
        choices=NimbusExperiment.DocumentationLink.choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    link = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = NimbusDocumentationLink
        fields = ("title", "link")


class OverviewForm(NimbusChangeLogFormMixin, forms.ModelForm):
    YES_NO_CHOICES = (
        (True, "Yes"),
        (False, "No"),
    )

    name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    hypothesis = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control"})
    )
    risk_brand = forms.TypedChoiceField(
        required=False,
        choices=YES_NO_CHOICES,
        widget=InlineRadioSelect,
        coerce=lambda x: x == "True",
    )
    risk_message = forms.TypedChoiceField(
        required=False,
        choices=YES_NO_CHOICES,
        widget=InlineRadioSelect,
        coerce=lambda x: x == "True",
    )
    projects = forms.ModelMultipleChoiceField(
        required=False, queryset=Project.objects.all(), widget=MultiSelectWidget()
    )
    public_description = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )
    risk_revenue = forms.TypedChoiceField(
        required=False,
        choices=YES_NO_CHOICES,
        widget=InlineRadioSelect,
        coerce=lambda x: x == "True",
    )
    risk_partner_related = forms.TypedChoiceField(
        required=False,
        choices=YES_NO_CHOICES,
        widget=InlineRadioSelect,
        coerce=lambda x: x == "True",
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "name",
            "hypothesis",
            "projects",
            "public_description",
            "risk_partner_related",
            "risk_revenue",
            "risk_brand",
            "risk_message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.NimbusDocumentationLinkFormSet = inlineformset_factory(
            NimbusExperiment,
            NimbusDocumentationLink,
            form=NimbusDocumentationLinkForm,
            extra=0,  # Number of empty forms to display initially
        )
        self.documentation_links = self.NimbusDocumentationLinkFormSet(
            data=self.data or None,
            instance=self.instance,
        )

    def is_valid(self):
        return super().is_valid() and self.documentation_links.is_valid()

    def save(self):
        experiment = super().save()
        self.documentation_links.save()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} updated overview"


class DocumentationLinkCreateForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = []

    def save(self):
        super().save(commit=False)
        self.instance.documentation_links.create()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} added a documentation link"


class DocumentationLinkDeleteForm(NimbusChangeLogFormMixin, forms.ModelForm):
    link_id = forms.ModelChoiceField(queryset=NimbusDocumentationLink.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = ["link_id"]

    def save(self):
        super().save(commit=False)
        documentation_link = self.cleaned_data["link_id"]
        documentation_link.delete()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} removed a documentation link"


class MetricsForm(NimbusChangeLogFormMixin, forms.ModelForm):
    primary_outcomes = forms.MultipleChoiceField(
        required=False, widget=MultiSelectWidget(attrs={"data-max-options": 2})
    )
    secondary_outcomes = forms.MultipleChoiceField(
        required=False, widget=MultiSelectWidget()
    )
    segments = forms.MultipleChoiceField(required=False, widget=MultiSelectWidget())

    class Meta:
        model = NimbusExperiment
        fields = [
            "primary_outcomes",
            "secondary_outcomes",
            "segments",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        application_outcomes = sorted(
            [
                (o.slug, o.friendly_name)
                for o in Outcomes.by_application(self.instance.application)
            ]
        )
        self.fields["primary_outcomes"].choices = application_outcomes
        self.fields["secondary_outcomes"].choices = application_outcomes

        application_segments = sorted(
            [
                (s.slug, s.friendly_name)
                for s in Segments.by_application(self.instance.application)
            ]
        )
        self.fields["segments"].choices = application_segments

    def get_changelog_message(self):
        return f"{self.request.user} updated metrics"


class AudienceForm(NimbusChangeLogFormMixin, forms.ModelForm):
    def get_experiment_branch_choices():
        return sorted(
            [
                branch_choice
                for experiment in NimbusExperiment.objects.exclude(is_archived=True)
                for branch_choice in experiment.branch_choices()
            ]
        )

    def get_targeting_config_choices():
        return sorted(
            [
                (targeting.slug, f"{targeting.name} - {targeting.description}")
                for targeting in NimbusTargetingConfig.targeting_configs
            ],
        )

    channel = forms.ChoiceField(
        required=False,
        label="",
        choices=NimbusExperiment.Channel.choices,
        widget=forms.widgets.Select(
            attrs={
                "class": "form-select",
            },
        ),
    )
    firefox_min_version = forms.ChoiceField(
        required=False,
        label="",
        choices=NimbusExperiment.Version.choices,
        widget=forms.widgets.Select(
            attrs={
                "class": "form-select",
            },
        ),
    )
    firefox_max_version = forms.ChoiceField(
        required=False,
        label="",
        choices=NimbusExperiment.Version.choices,
        widget=forms.widgets.Select(
            attrs={
                "class": "form-select",
            },
        ),
    )
    locales = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Locale.objects.all().order_by("code"),
        widget=MultiSelectWidget(),
    )
    languages = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Language.objects.all().order_by("code"),
        widget=MultiSelectWidget(),
    )
    countries = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Country.objects.all().order_by("code"),
        widget=MultiSelectWidget(),
    )
    targeting_config_slug = forms.ChoiceField(
        required=False,
        label="",
        choices=get_targeting_config_choices,
        widget=forms.widgets.Select(
            attrs={
                "class": "form-select",
            },
        ),
    )
    excluded_experiments_branches = forms.MultipleChoiceField(
        required=False,
        choices=get_experiment_branch_choices,
        widget=MultiSelectWidget(),
    )
    required_experiments_branches = forms.MultipleChoiceField(
        required=False,
        choices=get_experiment_branch_choices,
        widget=MultiSelectWidget(),
    )
    is_sticky = forms.BooleanField(required=False)
    population_percent = forms.DecimalField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    total_enrolled_clients = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    proposed_enrollment = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    proposed_duration = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "channel",
            "countries",
            "excluded_experiments_branches",
            "firefox_max_version",
            "firefox_min_version",
            "is_sticky",
            "languages",
            "locales",
            "population_percent",
            "proposed_duration",
            "proposed_enrollment",
            "required_experiments_branches",
            "targeting_config_slug",
            "total_enrolled_clients",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_initial_experiments_branches("required_experiments_branches")
        self.setup_initial_experiments_branches("excluded_experiments_branches")

    def setup_initial_experiments_branches(self, field_name):
        self.initial[field_name] = [
            branch.child_experiment.format_branch_choice(branch.branch_slug)[0]
            for branch in getattr(self.instance, field_name)
        ]

    def save_experiments_branches(self, field_name, model):
        experiments_branches = self.cleaned_data.pop(field_name)

        if experiments_branches is not None:
            model.objects.filter(parent_experiment=self.instance).all().delete()
            for experiment_branch in experiments_branches:
                experiment_slug, branch_slug = experiment_branch.split(":")
                if branch_slug.strip() == "None":
                    branch_slug = None
                model.objects.create(
                    parent_experiment=self.instance,
                    child_experiment=NimbusExperiment.objects.get(slug=experiment_slug),
                    branch_slug=branch_slug,
                )

    def save(self, *args, **kwargs):
        self.save_experiments_branches(
            "required_experiments_branches", NimbusExperimentBranchThroughRequired
        )
        self.save_experiments_branches(
            "excluded_experiments_branches", NimbusExperimentBranchThroughExcluded
        )
        return super().save(*args, **kwargs)

    def get_changelog_message(self):
        return f"{self.request.user} updated audience"


class SubscribeForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = []

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.subscribers.add(self.request.user)
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} added subscriber"


class UnsubscribeForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = []

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.subscribers.remove(self.request.user)
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} removed subscriber"


class UpdateStatusForm(NimbusChangeLogFormMixin, forms.ModelForm):
    status = None
    status_next = None
    publish_status = None

    class Meta:
        model = NimbusExperiment
        fields = []

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.status = self.status
        experiment.status_next = self.status_next
        experiment.publish_status = self.publish_status
        experiment.save()
        # Allocate bucket range if needed
        if experiment.has_filter(NimbusExperiment.Filters.SHOULD_ALLOCATE_BUCKETS):
            experiment.allocate_bucket_range()

        if experiment.should_call_preview_task:
            nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)

        if experiment.should_call_push_task:
            collection = experiment.kinto_collection
            nimbus_check_kinto_push_queue_by_collection.apply_async(
                countdown=5, args=[collection]
            )

        return experiment


class DraftToPreviewForm(UpdateStatusForm):
    status = NimbusExperiment.Status.PREVIEW
    status_next = NimbusExperiment.Status.PREVIEW
    publish_status = NimbusExperiment.PublishStatus.IDLE

    def get_changelog_message(self):
        return f"{self.request.user} launched experiment to Preview"


class DraftToReviewForm(UpdateStatusForm):
    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW

    def get_changelog_message(self):
        return f"{self.request.user} requested launch without Preview"


class PreviewToReviewForm(UpdateStatusForm):
    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW

    def get_changelog_message(self):
        return f"{self.request.user} requested launch from Preview"


class PreviewToDraftForm(UpdateStatusForm):
    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.DRAFT
    publish_status = NimbusExperiment.PublishStatus.IDLE

    def get_changelog_message(self):
        return f"{self.request.user} moved the experiment back to Draft"


class ReviewToDraftForm(UpdateStatusForm):
    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.DRAFT
    publish_status = NimbusExperiment.PublishStatus.IDLE

    def get_changelog_message(self):
        return f"{self.request.user} cancelled the review"


class ReviewToApproveForm(UpdateStatusForm):
    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the review."


class ReviewToRejectForm(UpdateStatusForm):
    status = NimbusExperiment.Status.DRAFT
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    changelog_message = forms.CharField(
        required=True, label="Reason for Rejection", max_length=1000
    )

    def get_changelog_message(self):
        changelog_message = self.cleaned_data.get("changelog_message", "")
        return f"{self.request.user} rejected the review with reason: {changelog_message}"
