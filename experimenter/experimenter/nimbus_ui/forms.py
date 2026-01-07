import random
from collections import defaultdict
from datetime import UTC, datetime

import markus
from django import forms
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Case, When
from django.forms import BaseInlineFormSet, BaseModelFormSet, inlineformset_factory
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_summernote.widgets import SummernoteWidget

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusBranchScreenshot,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
    NimbusFeatureConfig,
    Tag,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.klaatu.tasks import klaatu_start_job
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.outcomes import Outcomes
from experimenter.segments import Segments
from experimenter.slack.tasks import nimbus_send_slack_notification
from experimenter.targeting.constants import NimbusTargetingConfig

metrics = markus.get_metrics("experimenter.nimbus_ui_forms")


class NimbusChangeLogFormMixin:
    def __init__(self, *args, request: HttpRequest = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def get_changelog_message(self) -> str:
        raise NotImplementedError

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if type(experiment) is NimbusBranchScreenshot:
            experiment = self.instance.branch.experiment

        generate_nimbus_changelog(
            experiment, self.request.user, self.get_changelog_message()
        )
        metrics.incr("changelog_form.save", tags=[f"form:{type(self).__name__}"])
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
        return f"{self.request.user} created {self.cleaned_data['name']}"

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

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if experiment.branches.count() == 0:
            control = experiment.branches.create(name="Control", slug="control", ratio=1)
            experiment.branches.create(name="Treatment A", slug="treatment-a", ratio=1)
            experiment.reference_branch = control
            experiment.save(update_fields=["reference_branch"])

        return experiment


class NimbusExperimentSidebarCloneForm(NimbusChangeLogFormMixin, forms.ModelForm):
    owner = forms.ModelChoiceField(
        User.objects.all(),
        widget=forms.widgets.HiddenInput(),
    )
    name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    slug = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput(),
    )

    class Meta:
        model = NimbusExperiment
        fields = ["owner", "name", "slug"]

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)
        if not slug:
            raise forms.ValidationError(NimbusUIConstants.ERROR_NAME_INVALID)
        if NimbusExperiment.objects.filter(slug=slug).exists():
            raise forms.ValidationError(
                NimbusUIConstants.ERROR_NAME_MAPS_TO_EXISTING_SLUG
            )
        return name

    def clean(self):
        cleaned_data = super().clean()
        if "name" in cleaned_data:
            cleaned_data["slug"] = slugify(cleaned_data["name"])
        return cleaned_data

    def get_changelog_message(self):
        return f"{self.request.user} cloned this experiment from {self.instance.name}"

    @transaction.atomic
    def save(self):
        return self.instance.clone(self.cleaned_data["name"], self.cleaned_data["owner"])


class NimbusExperimentPromoteToRolloutForm(
    NimbusExperimentSidebarCloneForm, NimbusChangeLogFormMixin, forms.ModelForm
):
    owner = forms.ModelChoiceField(
        User.objects.all(),
        widget=forms.widgets.HiddenInput(),
    )
    name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    slug = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput(),
    )
    branch_slug = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = NimbusExperiment
        fields = ["owner", "name", "slug"]

    @transaction.atomic
    def save(self):
        return self.instance.clone(
            self.cleaned_data["name"],
            self.cleaned_data["owner"],
            self.cleaned_data["branch_slug"],
        )


class ToggleArchiveForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = []

    @transaction.atomic
    def save(self):
        self.instance.is_archived = not self.instance.is_archived
        super().save()
        return self.instance

    def get_changelog_message(self):
        return (
            f"{self.request.user} set the Is Archived Flag to {self.instance.is_archived}"
        )


class QAStatusForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = [
            "qa_status",
            "qa_comment",
            "qa_run_test_plan_url",
            "qa_run_testrail_url",
        ]
        widgets = {
            "qa_status": forms.Select(choices=NimbusExperiment.QAStatus),
            "qa_run_test_plan_url": forms.URLInput(attrs={"class": "form-control"}),
            "qa_run_testrail_url": forms.URLInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_qa_status = self.instance.qa_status if self.instance.pk else None

    @transaction.atomic
    def save(self, *args, **kwargs):
        new_qa_status = self.cleaned_data.get("qa_status")
        if self._initial_qa_status != new_qa_status:
            if new_qa_status != NimbusExperiment.QAStatus.NOT_SET:
                self.instance.qa_run_date = timezone.now().date()

        return super().save(*args, **kwargs)

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


class SingleSelectWidget(forms.Select):
    class_attrs = "selectpicker form-control"

    def __init__(self, *args, attrs=None, **kwargs):
        attrs = attrs or {}
        attrs.update(
            {
                "class": self.class_attrs,
                "data-live-search": "true",
                "data-live-search-placeholder": "Search",
                "data-max-options": 1,
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

    @transaction.atomic
    def save(self):
        experiment = super().save()
        self.documentation_links.save()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} updated overview"


class DocumentationLinkCreateForm(OverviewForm):
    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.instance.documentation_links.create()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} added a documentation link"


class DocumentationLinkDeleteForm(OverviewForm):
    link_id = forms.ModelChoiceField(queryset=NimbusDocumentationLink.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = [*OverviewForm.Meta.fields, "link_id"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        documentation_link = self.cleaned_data["link_id"]
        documentation_link.delete()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} removed a documentation link"


class NimbusBranchFeatureValueForm(forms.ModelForm):
    value = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "value-editor"}),
    )

    class Meta:
        model = NimbusBranchFeatureValue
        fields = ("value",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance._state.adding and (
            self.instance.value is None or self.instance.value == {}
        ):
            self.fields["value"].initial = ""

        if (
            self.instance is not None
            and self.instance.branch_id is not None
            and self.instance.branch.experiment
            and self.instance.branch.experiment.application
            != NimbusExperiment.Application.DESKTOP
        ):
            self.fields["value"].widget.attrs["data-experiment-slug"] = (
                self.instance.branch.experiment.slug
            )

            if self.instance.feature_config:
                self.fields["value"].widget.attrs["data-feature-slug"] = (
                    self.instance.feature_config.slug
                )

        if (
            self.instance.id is not None
            and self.instance.feature_config
            and (
                schema := self.instance.feature_config.schemas.filter(
                    version=None
                ).first()
            )
            and schema is not None
            and schema.schema is not None
        ):
            self.fields["value"].widget.attrs.update(
                {
                    "data-schema": schema.schema,
                }
            )

    def clean_value(self):
        value = self.cleaned_data.get("value")

        if not value or value.strip() == "":
            return "{}"
        return value


class NimbusBranchScreenshotForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = NimbusBranchScreenshot
        fields = ("image", "description")


class NimbusBranchForm(forms.ModelForm):
    name = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    slug = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput(),
    )
    description = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    ratio = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = NimbusBranch
        fields = ("name", "description", "ratio", "slug")

    def __init__(self, *args, prefix=None, **kwargs):
        super().__init__(*args, prefix=prefix, **kwargs)

        self.NimbusNimbusBranchFeatureValueFormSet = inlineformset_factory(
            NimbusBranch,
            NimbusBranchFeatureValue,
            form=NimbusBranchFeatureValueForm,
            extra=0,
        )
        self.branch_feature_values = self.NimbusNimbusBranchFeatureValueFormSet(
            data=self.data or None,
            instance=self.instance,
            prefix=f"{prefix}-feature-value",
        )

        self.NimbusBranchScreenshotFormSet = inlineformset_factory(
            NimbusBranch,
            NimbusBranchScreenshot,
            form=NimbusBranchScreenshotForm,
            extra=0,
        )

        screenshot_formset_args = {
            "data": self.data or None,
            "instance": self.instance,
            "prefix": f"{prefix}-screenshots" if prefix else None,
        }

        if self.files:
            screenshot_formset_args["files"] = self.files

        self.screenshot_formset = self.NimbusBranchScreenshotFormSet(
            **screenshot_formset_args,
        )

    @property
    def errors(self):
        errors = super().errors
        if any(self.branch_feature_values.errors):
            errors["branch_feature_values"] = self.branch_feature_values.errors
        if any(self.screenshot_formset.errors):
            errors["screenshots"] = self.screenshot_formset.errors
        return errors

    def is_valid(self):
        return (
            super().is_valid()
            and self.branch_feature_values.is_valid()
            and self.screenshot_formset.is_valid()
        )

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)
        if not slug:
            raise forms.ValidationError(NimbusUIConstants.ERROR_NAME_INVALID)
        if (
            NimbusBranch.objects.exclude(id=self.instance.id)
            .filter(experiment=self.instance.experiment, slug=slug)
            .exists()
        ):
            raise forms.ValidationError(NimbusUIConstants.ERROR_SLUG_DUPLICATE_BRANCH)
        return name

    def clean(self):
        cleaned_data = super().clean()
        if "name" in cleaned_data:
            cleaned_data["slug"] = slugify(cleaned_data["name"])
        return cleaned_data

    @transaction.atomic
    def save(self, *args, **kwargs):
        branch = super().save(*args, **kwargs)
        self.branch_feature_values.save()
        self.screenshot_formset.save()
        return branch


class FeatureConfigMultiSelectWidget(MultiSelectWidget):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        option["attrs"]["data-subtext"] = value.instance.description
        return option


class FeatureConfigModelChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class OrderedBranchFormSet(BaseInlineFormSet):
    """
    Branch FormSet with reference branch first and remaining
    branches ordered by db id for stable ordering
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .order_by(
                Case(When(id=self.instance.reference_branch_id, then=0), default=1),
                "id",
            )
        )


class NimbusBranchesForm(NimbusChangeLogFormMixin, forms.ModelForm):
    feature_configs = FeatureConfigModelChoiceField(
        required=False,
        queryset=NimbusFeatureConfig.objects.all(),
        widget=FeatureConfigMultiSelectWidget(attrs={}),
    )

    is_firefox_labs_opt_in = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    firefox_labs_title = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    firefox_labs_description = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    firefox_labs_description_links = forms.CharField(
        required=False, widget=forms.HiddenInput()
    )
    firefox_labs_group = forms.ChoiceField(
        required=False,
        choices=NimbusExperiment.FirefoxLabsGroups.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    requires_restart = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    update_on_change_fields = (
        "equal_branch_ratio",
        "feature_configs",
        "is_firefox_labs_opt_in",
        "is_localized",
        "is_rollout",
    )

    class Meta:
        model = NimbusExperiment
        fields = (
            "equal_branch_ratio",
            "feature_configs",
            "is_localized",
            "is_rollout",
            "localizations",
            "prevent_pref_conflicts",
            "warn_feature_schema",
            "is_firefox_labs_opt_in",
            "firefox_labs_title",
            "firefox_labs_description",
            "firefox_labs_description_links",
            "firefox_labs_group",
            "requires_restart",
        )
        widgets = {
            "is_rollout": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "warn_feature_schema": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "equal_branch_ratio": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "prevent_pref_conflicts": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "is_localized": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "localizations": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        branches_formset_kwargs = {
            "data": self.data or None,
            "instance": self.instance,
        }
        if self.files:
            branches_formset_kwargs["files"] = self.files

        NimbusBranchFormSet = inlineformset_factory(
            NimbusExperiment,
            NimbusBranch,
            form=NimbusBranchForm,
            formset=OrderedBranchFormSet,
            extra=0,
        )

        self.branches = NimbusBranchFormSet(**branches_formset_kwargs)

        self.fields["feature_configs"].queryset = NimbusFeatureConfig.objects.filter(
            application=self.instance.application
        ).order_by("slug")

        show_errors = ""
        if (
            hasattr(self, "request")
            and self.request
            and self.request.GET.get("show_errors") == "true"
        ):
            show_errors = "?show_errors=true"

        base_url = reverse(
            "nimbus-ui-partial-update-branches",
            kwargs={"slug": self.instance.slug},
        )

        update_on_change_attrs = {
            "hx-post": f"{base_url}{show_errors}",
            "hx-trigger": "change",
            "hx-select": "#branches-form",
            "hx-target": "#branches-form",
        }

        for field in self.update_on_change_fields:
            self.fields[field].widget.attrs.update(update_on_change_attrs)

        self.was_labs_opt_in = self.instance.is_firefox_labs_opt_in

        if self.instance.is_rollout:
            self.fields["prevent_pref_conflicts"].disabled = True

    @property
    def errors(self):
        errors = super().errors
        if any(self.branches.errors):
            errors["branches"] = self.branches.errors
        return errors

    def clean(self):
        cleaned_data = super().clean()

        if not self.was_labs_opt_in and cleaned_data["is_firefox_labs_opt_in"]:
            cleaned_data["is_rollout"] = True
        elif not cleaned_data["is_rollout"]:
            cleaned_data["is_firefox_labs_opt_in"] = False

        if not cleaned_data["is_firefox_labs_opt_in"]:
            cleaned_data["firefox_labs_title"] = ""
            cleaned_data["firefox_labs_description"] = ""
            cleaned_data["firefox_labs_description_links"] = "null"
            cleaned_data["firefox_labs_group"] = ""
            cleaned_data["requires_restart"] = False

        if cleaned_data["is_rollout"]:
            cleaned_data["prevent_pref_conflicts"] = True

        return cleaned_data

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        self.branches.save()

        if experiment.is_rollout:
            branches = experiment.branches.all()

            if experiment.reference_branch:
                branches = branches.exclude(id=experiment.reference_branch.id)

            branches.delete()

        saved_experiment_feature_configs = set(experiment.feature_configs.all())
        saved_branch_feature_configs = {
            feature_value.feature_config
            for feature_value in NimbusBranchFeatureValue.objects.filter(
                branch__experiment=experiment
            )
        }
        new_feature_configs = (
            saved_experiment_feature_configs - saved_branch_feature_configs
        )
        deleted_feature_configs = (
            saved_branch_feature_configs - saved_experiment_feature_configs
        )

        for branch in experiment.branches.all():
            branch.feature_values.filter(
                feature_config__in=deleted_feature_configs
            ).delete()

            for feature_config in new_feature_configs:
                branch.feature_values.create(feature_config=feature_config, value="{}")

        if experiment.equal_branch_ratio:
            experiment.branches.all().update(ratio=1)

        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} updated branches"


class NimbusBranchCreateForm(NimbusBranchesForm):
    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        if not experiment.reference_branch:
            name = "Control"
        else:
            branch_names_all = [f"Treatment {chr(i)}" for i in range(65, 91)]
            branch_names_used = experiment.branches.values_list("name", flat=True)
            branch_names_free = sorted(set(branch_names_all) - set(branch_names_used))
            name = branch_names_free[0]

        slug = slugify(name)
        branch = experiment.branches.create(name=name, slug=slug)

        if not experiment.reference_branch:
            experiment.reference_branch = branch
            experiment.save()

        for feature_config in experiment.feature_configs.all():
            branch.feature_values.create(feature_config=feature_config)

        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} added a branch"


class NimbusBranchDeleteForm(NimbusBranchesForm):
    branch_id = forms.ModelChoiceField(queryset=NimbusBranch.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = [
            "branch_id",
            *NimbusBranchesForm.Meta.fields,
        ]

    def clean_branch_id(self):
        branch = self.cleaned_data["branch_id"]
        if branch == self.instance.reference_branch:
            raise forms.ValidationError("You cannot delete the reference branch.")
        return branch

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        branch = self.cleaned_data["branch_id"]
        branch.delete()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} removed a branch"


class BranchScreenshotCreateForm(NimbusBranchesForm):
    branch_id = forms.ModelChoiceField(queryset=NimbusBranch.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = [
            "branch_id",
            *NimbusBranchesForm.Meta.fields,
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        branch = self.cleaned_data["branch_id"]
        branch.screenshots.create()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} added a branch screenshot"


class BranchScreenshotDeleteForm(NimbusBranchesForm):
    screenshot_id = forms.ModelChoiceField(queryset=NimbusBranchScreenshot.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = [
            "screenshot_id",
            *NimbusBranchesForm.Meta.fields,
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        screenshot = self.cleaned_data["screenshot_id"]
        screenshot.delete()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} removed a branch screenshot"


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
    def get_version_choices():
        return [
            (
                NimbusExperiment.Version.NO_VERSION.value,
                NimbusExperiment.Version.NO_VERSION.label,
            ),
            *NimbusExperiment.Version.choices[1:][::-1],
        ]

    def get_targeting_config_choices(self):
        application_name = NimbusExperiment.Application(self.instance.application).name
        return sorted(
            [
                (targeting.slug, f"{targeting.name} - {targeting.description}")
                for targeting in NimbusTargetingConfig.targeting_configs
                if application_name in targeting.application_choice_names
            ],
            key=lambda choice: choice[1].lower(),
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
    channels = forms.MultipleChoiceField(
        required=False,
        label="",
        choices=NimbusExperiment.Channel.choices,
        widget=MultiSelectWidget(),
    )
    firefox_min_version = forms.ChoiceField(
        required=False,
        label="",
        choices=get_version_choices,
        widget=forms.widgets.Select(
            attrs={
                "class": "form-select",
            },
        ),
    )
    firefox_max_version = forms.ChoiceField(
        required=False,
        label="",
        choices=get_version_choices,
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
    exclude_locales = forms.BooleanField(required=False)
    languages = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Language.objects.all().order_by("code"),
        widget=MultiSelectWidget(),
    )
    exclude_languages = forms.BooleanField(required=False)
    countries = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Country.objects.all().order_by("code"),
        widget=MultiSelectWidget(),
    )
    exclude_countries = forms.BooleanField(required=False)
    targeting_config_slug = forms.ChoiceField(
        required=False,
        label="",
        widget=SingleSelectWidget(),
    )

    excluded_experiments_branches = forms.MultipleChoiceField(
        required=False,
        widget=MultiSelectWidget(),
    )
    required_experiments_branches = forms.MultipleChoiceField(
        required=False,
        widget=MultiSelectWidget(),
    )
    is_sticky = forms.BooleanField(required=False)
    is_first_run = forms.BooleanField(required=False)
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
    proposed_release_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "channel",
            "channels",
            "countries",
            "exclude_countries",
            "exclude_languages",
            "exclude_locales",
            "excluded_experiments_branches",
            "firefox_max_version",
            "firefox_min_version",
            "is_first_run",
            "is_sticky",
            "languages",
            "locales",
            "population_percent",
            "proposed_duration",
            "proposed_enrollment",
            "proposed_release_date",
            "required_experiments_branches",
            "targeting_config_slug",
            "total_enrolled_clients",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["targeting_config_slug"].choices = self.get_targeting_config_choices()
        self.setup_experiment_branch_choices()
        self.setup_initial_experiments_branches("required_experiments_branches")
        self.setup_initial_experiments_branches("excluded_experiments_branches")
        self.setup_channel_choices()

        self.fields["is_first_run"].widget.attrs.update(
            {
                "hx-post": reverse(
                    "nimbus-ui-update-audience", kwargs={"slug": self.instance.slug}
                ),
                "hx-trigger": "change",
                "hx-select": "#first-run-fields",
                "hx-target": "#first-run-fields",
            }
        )

        # If this is a live rollout, restrict edits to only population_percent
        if self.instance.is_live_rollout:
            for field_name in self.fields:
                if field_name != "population_percent":
                    self.fields[field_name].disabled = True

    def format_branch_choice(self, experiment_slug, experiment_name, branch_slug):
        if branch_slug is None:
            return f"{experiment_slug}:None", f"{experiment_name} (All branches)"
        return (
            f"{experiment_slug}:{branch_slug}",
            f"{experiment_name} ({branch_slug.capitalize()})",
        )

    def setup_experiment_branch_choices(self):
        branch_slugs = (
            NimbusBranch.objects.filter(
                experiment__application=self.instance.application,
                experiment__is_archived=False,
            )
            .exclude(experiment__id=self.instance.id)
            .values_list("experiment__slug", "experiment__name", "slug")
        )

        branches_by_experiment_slug = defaultdict(list)
        for experiment_slug, experiment_name, branch_slug in branch_slugs:
            branches_by_experiment_slug[(experiment_slug, experiment_name)].append(
                branch_slug
            )

        all_choices = []
        for (experiment_slug, experiment_name), branch_slugs in sorted(
            branches_by_experiment_slug.items()
        ):
            all_choices.append(
                self.format_branch_choice(experiment_slug, experiment_name, None)
            )
            for branch_slug in sorted(branch_slugs):
                all_choices.append(
                    self.format_branch_choice(
                        experiment_slug, experiment_name, branch_slug
                    )
                )

        self.fields["excluded_experiments_branches"].choices = all_choices
        self.fields["required_experiments_branches"].choices = all_choices

    def setup_initial_experiments_branches(self, field_name):
        self.initial[field_name] = [
            self.format_branch_choice(
                branch.child_experiment.slug,
                branch.child_experiment.name,
                branch.branch_slug,
            )[0]
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

    def setup_channel_choices(self):
        self.fields["channel"].choices = [
            (channel.value, channel.label)
            for channel in NimbusExperiment.Channel
            if channel in self.instance.application_config.channel_app_id
        ]

        self.fields["channels"].choices = [
            (channel.value, channel.label)
            for channel in NimbusExperiment.Channel
            if (
                channel in self.instance.application_config.channel_app_id
                and channel != NimbusExperiment.Channel.NO_CHANNEL
            )
        ]

    def check_rollout_dirty(self, instance):
        if not instance.is_rollout:
            return

        population_changed = (
            "population_percent" in self.changed_data
            and self.cleaned_data.get("population_percent")
            != self.initial.get("population_percent")
        )

        publish_status = (
            self.cleaned_data.get("publish_status") or instance.publish_status
        )

        if (
            population_changed
            and instance.is_rollout
            and instance.status == NimbusExperiment.Status.LIVE
            and instance.status_next is None
            and instance.publish_status == NimbusExperiment.PublishStatus.IDLE
            and publish_status != NimbusExperiment.PublishStatus.REVIEW
        ):
            instance.is_rollout_dirty = True

    @transaction.atomic
    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        self.check_rollout_dirty(instance)
        if instance.is_rollout_dirty:
            instance.save(update_fields=["is_rollout_dirty"])
        self.save_experiments_branches(
            "required_experiments_branches", NimbusExperimentBranchThroughRequired
        )
        self.save_experiments_branches(
            "excluded_experiments_branches", NimbusExperimentBranchThroughExcluded
        )
        return instance

    def get_changelog_message(self):
        return f"{self.request.user} updated audience"


class SubscribeForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = []

    @transaction.atomic
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

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.subscribers.remove(self.request.user)
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} removed subscriber"


class ToggleReviewSlackNotificationsForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ["enable_review_slack_notifications"]

    def get_changelog_message(self):
        status = (
            "enabled"
            if self.cleaned_data.get("enable_review_slack_notifications")
            else "disabled"
        )
        return f"{self.request.user} {status} review Slack notifications"


class SlackNotificationMixin:
    slack_action = None

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        if self.slack_action:
            if experiment.enable_review_slack_notifications:
                nimbus_send_slack_notification.delay(
                    experiment_id=experiment.id,
                    email_addresses=experiment.notification_emails,
                    action_text=NimbusConstants.SLACK_FORM_ACTIONS[self.slack_action],
                    requesting_user_email=self.request.user.email,
                )
        return experiment


class UpdateStatusForm(NimbusChangeLogFormMixin, forms.ModelForm):
    status = None
    status_next = None
    publish_status = None
    is_paused = None

    required_status = None
    required_status_next = None
    required_publish_status = None
    required_is_paused = None

    class Meta:
        model = NimbusExperiment
        fields = []

    def clean(self):
        cleaned_data = super().clean()

        required_state = (
            self.required_status,
            self.required_status_next,
            self.required_publish_status,
            self.required_is_paused,
        )
        current_state = (
            self.instance.status,
            self.instance.status_next,
            self.instance.publish_status,
            self.instance.is_paused,
        )

        state_mismatch = (
            self.required_status != self.instance.status
            or self.required_status_next != self.instance.status_next
            or self.required_publish_status != self.instance.publish_status
            or (
                self.required_is_paused is not None
                and self.required_is_paused != self.instance.is_paused
            )
        )

        if state_mismatch:
            raise forms.ValidationError(
                NimbusUIConstants.ERROR_INVALID_STATE_TRANSITION.format(
                    required_state=required_state,
                    current_state=current_state,
                )
            )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        self.instance.status = self.status
        self.instance.status_next = self.status_next
        previous_publish_status = self.instance.publish_status
        self.instance.publish_status = self.publish_status

        if self.is_paused is not None:
            self.instance.is_paused = self.is_paused

        if self.status == NimbusExperiment.Status.DRAFT:
            self.instance.published_dto = None

        if (
            previous_publish_status == NimbusExperiment.PublishStatus.REVIEW
            and self.publish_status != NimbusExperiment.PublishStatus.REVIEW
        ):
            last_review_request = self.instance.changes.latest_review_request()
            if last_review_request is not None:
                delta = datetime.now(UTC) - last_review_request.changed_on
                delta_ms = int(delta.total_seconds() * 1000)
                metrics.timing(
                    "review_timing",
                    value=delta_ms,
                    tags=[f"status:{self.publish_status}"],
                )

        return super().save(commit=commit)


class DraftToPreviewForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE
    required_is_paused = False

    status = NimbusExperiment.Status.PREVIEW
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    is_paused = False

    def get_changelog_message(self):
        return f"{self.request.user} launched experiment to Preview"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.allocate_bucket_range()
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        klaatu_start_job.delay(experiment_id=experiment.id)
        return experiment


class DraftToReviewForm(SlackNotificationMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE
    required_is_paused = False

    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    is_paused = False

    slack_action = NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested launch without Preview"


class PreviewToReviewForm(SlackNotificationMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.PREVIEW
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE
    required_is_paused = False

    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    is_paused = False

    slack_action = NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested launch from Preview"


class PreviewToDraftForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.PREVIEW
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE
    required_is_paused = False

    status = NimbusExperiment.Status.DRAFT
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    is_paused = False

    def get_changelog_message(self):
        return f"{self.request.user} moved the experiment back to Draft"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        return experiment


class ReviewToDraftForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = False

    status = NimbusExperiment.Status.DRAFT
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    is_paused = False

    changelog_message = forms.CharField(
        required=False, label="Changelog Message", max_length=1000
    )

    cancel_message = forms.CharField(
        required=False, label="Cancel Message", max_length=1000
    )

    def get_changelog_message(self):
        if self.cleaned_data.get("changelog_message"):
            return (
                f"{self.request.user} rejected the review with reason: "
                f"{self.cleaned_data['changelog_message']}"
            )
        return f"{self.request.user} {self.cleaned_data['cancel_message']}"


class ReviewToApproveForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = False

    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED
    is_paused = False

    def get_changelog_message(self):
        return f"{self.request.user} approved the review."

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.allocate_bucket_range()
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )

        return experiment


class LiveToEndEnrollmentForm(SlackNotificationMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE
    required_is_paused = False

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    is_paused = True

    slack_action = NimbusConstants.SLACK_ACTION_END_ENROLLMENT_REQUEST

    def clean(self):
        cleaned_data = super().clean()

        if self.instance and self.instance.is_rollout_dirty:
            raise forms.ValidationError(NimbusExperiment.ERROR_CANNOT_PAUSE_UNPUBLISHED)

        if self.instance.is_rollout and not self.instance.is_firefox_labs_opt_in:
            raise forms.ValidationError(NimbusExperiment.ERROR_CANNOT_PAUSE_ROLLOUT)

        return cleaned_data

    def get_changelog_message(self):
        return f"{self.request.user} requested review to end enrollment"


class ApproveEndEnrollmentForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = True

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED
    is_paused = True

    def get_changelog_message(self):
        return f"{self.request.user} approved the end enrollment request"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        return experiment


class LiveToCompleteForm(SlackNotificationMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE
    required_is_paused = False

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.COMPLETE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    is_paused = False

    slack_action = NimbusConstants.SLACK_ACTION_END_EXPERIMENT_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested review to end experiment"


class ApproveEndExperimentForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.COMPLETE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = None

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.COMPLETE
    publish_status = NimbusExperiment.PublishStatus.APPROVED
    is_paused = True

    def get_changelog_message(self):
        return f"{self.request.user} approved the end experiment request"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        return experiment


class CancelEndEnrollmentForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = True

    status = NimbusExperiment.Status.LIVE
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    is_paused = False

    changelog_message = forms.CharField(
        required=False, label="Changelog Message", max_length=1000
    )

    cancel_message = forms.CharField(
        required=False, label="Cancel Message", max_length=1000
    )

    def get_changelog_message(self):
        if self.cleaned_data.get("changelog_message"):
            return (
                f"{self.request.user} rejected the review with reason: "
                f"{self.cleaned_data['changelog_message']}"
            )
        return f"{self.request.user} {self.cleaned_data['cancel_message']}"


class CancelEndExperimentForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.COMPLETE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = None

    status = NimbusExperiment.Status.LIVE
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE

    changelog_message = forms.CharField(
        required=False, label="Changelog Message", max_length=1000
    )

    cancel_message = forms.CharField(
        required=False, label="Cancel Message", max_length=1000
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_paused = self.instance.is_paused if self.instance else False

    def get_changelog_message(self):
        if self.cleaned_data.get("changelog_message"):
            return (
                f"{self.request.user} rejected the review with reason: "
                f"{self.cleaned_data['changelog_message']}"
            )
        return f"{self.request.user} {self.cleaned_data['cancel_message']}"


class LiveToUpdateRolloutForm(SlackNotificationMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE
    required_is_paused = False

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    is_paused = False

    slack_action = NimbusConstants.SLACK_ACTION_UPDATE_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested review to update Audience"


class CancelUpdateRolloutForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = False

    status = NimbusExperiment.Status.LIVE
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    is_paused = False

    changelog_message = forms.CharField(
        required=False, label="Changelog Message", max_length=1000
    )

    cancel_message = forms.CharField(
        required=False, label="Cancel Message", max_length=1000
    )

    def get_changelog_message(self):
        if self.cleaned_data.get("changelog_message"):
            return (
                f"{self.request.user} rejected the update review with reason: "
                f"{self.cleaned_data['changelog_message']}"
            )
        return f"{self.request.user} {self.cleaned_data['cancel_message']}"


class ApproveUpdateRolloutForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW
    required_is_paused = False

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED
    is_paused = False

    def get_changelog_message(self):
        return f"{self.request.user} approved the update review request"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.allocate_bucket_range()
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        return experiment


class FeaturesForm(forms.ModelForm):
    def get_feature_config_choices(self, application, qs):
        choices = [("", "Nothing selected")]
        choices.extend(
            sorted(
                [
                    (feature.pk, f"{feature.name} - {feature.description}")
                    for feature in qs
                ],
                key=lambda choice: choice[1].lower(),
            )
        )
        return choices

    application = forms.ChoiceField(
        required=False,
        choices=[("", "Nothing selected"), *list(NimbusExperiment.Application.choices)],
        widget=SingleSelectWidget(),
    )
    feature_configs = forms.ChoiceField(
        required=False,
        choices=[("", "Nothing selected")],
        widget=SingleSelectWidget(),
    )
    update_on_change_fields = ("application", "feature_configs")

    class Meta:
        model = NimbusFeatureConfig
        fields = ["application", "feature_configs"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Default: nothing selected for application and features
        selected_app = self.data.get("application") or self.initial.get("application")
        if selected_app:
            features = NimbusFeatureConfig.objects.filter(
                application=selected_app
            ).order_by("slug")
            self.fields["feature_configs"].choices = self.get_feature_config_choices(
                selected_app, features
            )

        self.fields["application"].initial = ""
        self.fields["feature_configs"].initial = ""

        base_url = reverse("nimbus-ui-features")
        htmx_attrs = {
            "hx-get": base_url,
            "hx-trigger": "change",
            "hx-include": "#features-form",
            "hx-select": "#features-form",
            "hx-target": "#features-form",
            "hx-swap": "outerHTML",
        }
        self.fields["application"].widget.attrs.update(htmx_attrs)
        self.fields["feature_configs"].widget.attrs.update(htmx_attrs)


class TagForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        max_length=100,
        label="Tag Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    color = forms.CharField(
        required=True,
        max_length=7,
        label="Color",
        widget=forms.TextInput(
            attrs={"type": "color", "class": "form-control form-control-color"}
        ),
    )

    class Meta:
        model = Tag
        fields = ["name", "color"]


class TagBaseFormSet(BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return

        names = []
        for form in self.forms:
            name = form.cleaned_data.get("name")
            if name:
                names.append(name.lower())

        if len(names) != len(set(names)):
            raise forms.ValidationError(NimbusUIConstants.ERROR_TAG_DUPLICATE_NAME)

    @transaction.atomic
    def create_tag(self):
        # Create a new tag with a unique name and random color
        base_name = "Tag"
        existing_count = Tag.objects.count()
        # Generate a range
        tag_names_all = [f"{base_name} {i}" for i in range(1, existing_count + 1)]
        tag_names_used = set(Tag.objects.values_list("name", flat=True))
        tag_names_free = sorted(set(tag_names_all) - tag_names_used)
        name = (
            tag_names_free[0] if tag_names_free else f"{base_name} {existing_count + 1}"
        )

        random_color = f"#{random.randint(0, 0xFFFFFF):06x}"
        tag = Tag.objects.create(name=name, color=random_color)
        return tag


TagFormSet = forms.modelformset_factory(
    Tag, form=TagForm, formset=TagBaseFormSet, extra=0, can_delete=False
)


class TagAssignForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ["tags"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tags"].queryset = Tag.objects.all().order_by("name")
        self.fields["tags"].widget = forms.CheckboxSelectMultiple()

    def get_changelog_message(self):
        return f"{self.request.user} updated tags"


class CollaboratorsForm(NimbusChangeLogFormMixin, forms.ModelForm):
    collaborators = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by("email"),
        widget=MultiSelectWidget(),
        required=False,
        label="Collaborators",
    )

    class Meta:
        model = NimbusExperiment
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the collaborators field with current subscribers
        if self.instance and self.instance.pk:
            self.fields["collaborators"].initial = self.instance.subscribers.all()

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        if commit:
            # Update subscribers with selected collaborators
            experiment.subscribers.set(self.cleaned_data["collaborators"])
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} updated collaborators"


class FeatureCollaboratorsForm(forms.ModelForm):
    collaborators = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by("email"),
        widget=MultiSelectWidget(),
        required=False,
        label="Subscribers",
    )

    class Meta:
        model = NimbusFeatureConfig
        fields = []

    def __init__(self, *args, request: HttpRequest = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        if self.instance and self.instance.pk:
            self.fields["collaborators"].initial = self.instance.subscribers.all()

    @transaction.atomic
    def save(self, commit=True):
        feature = super().save(commit=commit)
        if commit:
            feature.subscribers.set(self.cleaned_data["collaborators"])
        return feature


class EditOutcomeSummaryForm(NimbusChangeLogFormMixin, forms.ModelForm):
    takeaways_summary = forms.CharField(required=False, widget=SummernoteWidget())
    next_steps = forms.CharField(required=False, widget=SummernoteWidget())
    project_impact = forms.ChoiceField(
        required=False,
        choices=NimbusExperiment.ProjectImpact.choices,
        widget=forms.RadioSelect,
        label="Project Impact",
    )

    class Meta:
        model = NimbusExperiment
        fields = ["takeaways_summary", "next_steps", "project_impact"]

    def get_changelog_message(self):
        return f"{self.request.user} updated outcome summary"


class BranchLeadingScreenshotForm(NimbusChangeLogFormMixin, forms.ModelForm):
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = NimbusBranchScreenshot
        fields = ["image", "description"]

    def get_changelog_message(self):
        return (
            f"{self.request.user} updated leading screenshot for "
            f"{self.instance.branch.slug} branch"
        )
