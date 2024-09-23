from django import forms
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils.text import slugify

from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.models import NimbusExperiment
from experimenter.nimbus_ui_new.constants import NimbusUIConstants
from experimenter.outcomes import Outcomes


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
    def __init__(self, *args, attrs=None, **kwargs):
        attrs = attrs or {}
        attrs.update(
            {
                "class": "selectpicker form-control bg-body-tertiary",
                "data-live-search": "true",
                "data-live-search-placeholder": "Search",
            }
        )
        super().__init__(*args, attrs=attrs, **kwargs)


class MetricsForm(NimbusChangeLogFormMixin, forms.ModelForm):
    primary_outcomes = forms.MultipleChoiceField(
        required=False, widget=MultiSelectWidget(attrs={"data-max-options": 2})
    )
    secondary_outcomes = forms.MultipleChoiceField(
        required=False, widget=MultiSelectWidget()
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "primary_outcomes",
            "secondary_outcomes",
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

    def get_changelog_message(self):
        return f"{self.request.user} updated metrics"
