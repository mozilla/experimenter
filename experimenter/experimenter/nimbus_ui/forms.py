from collections import defaultdict

from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.http import HttpRequest
from django.urls import reverse
from django.utils.text import slugify

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusBranchScreenshot,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
    NimbusFeatureConfig,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
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


class DocumentationLinkCreateForm(OverviewForm):
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
            return None
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

    def clean(self):
        cleaned_data = super().clean()
        if "name" in cleaned_data:
            cleaned_data["slug"] = slugify(cleaned_data["name"])
        return cleaned_data

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

        self.NimbusBranchFormSet = inlineformset_factory(
            NimbusExperiment,
            NimbusBranch,
            form=NimbusBranchForm,
            extra=0,
        )

        branches_formset_kwargs = {
            "data": self.data or None,
            "instance": self.instance,
        }
        if self.files:
            branches_formset_kwargs["files"] = self.files

        self.branches = self.NimbusBranchFormSet(**branches_formset_kwargs)

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

        return cleaned_data

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
            "excluded_experiments_branches",
            "firefox_max_version",
            "firefox_min_version",
            "is_sticky",
            "is_first_run",
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
    is_paused = None

    class Meta:
        model = NimbusExperiment
        fields = []

    def save(self, commit=True):
        self.instance.status = self.status
        self.instance.status_next = self.status_next
        self.instance.publish_status = self.publish_status

        if self.is_paused is not None:
            self.instance.is_paused = self.is_paused

        if self.status == NimbusExperiment.Status.DRAFT:
            self.instance.published_dto = None

        return super().save(commit=commit)


class DraftToPreviewForm(UpdateStatusForm):
    status = NimbusExperiment.Status.PREVIEW
    status_next = NimbusExperiment.Status.PREVIEW
    publish_status = NimbusExperiment.PublishStatus.IDLE

    def get_changelog_message(self):
        return f"{self.request.user} launched experiment to Preview"

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.allocate_bucket_range()
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        return experiment


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

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        return experiment


class ReviewToDraftForm(UpdateStatusForm):
    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.DRAFT
    publish_status = NimbusExperiment.PublishStatus.IDLE
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
    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the review."

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.allocate_bucket_range()
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        return experiment


class LiveToEndEnrollmentForm(UpdateStatusForm):
    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    is_paused = True

    def get_changelog_message(self):
        return f"{self.request.user} requested review to end enrollment"


class ApproveEndEnrollmentForm(UpdateStatusForm):
    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the end enrollment request"

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        return experiment


class LiveToCompleteForm(UpdateStatusForm):
    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.COMPLETE
    publish_status = NimbusExperiment.PublishStatus.REVIEW

    def get_changelog_message(self):
        return f"{self.request.user} requested review to end experiment"


class ApproveEndExperimentForm(UpdateStatusForm):
    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.COMPLETE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the end experiment request"

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        return experiment


class CancelEndEnrollmentForm(UpdateStatusForm):
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


class LiveToUpdateRolloutForm(UpdateStatusForm):
    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW

    def get_changelog_message(self):
        return f"{self.request.user} requested review to update Audience"


class CancelUpdateRolloutForm(UpdateStatusForm):
    status = NimbusExperiment.Status.LIVE
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
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
    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the update review request"

    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.allocate_bucket_range()
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        return experiment


class FeaturesForm(forms.ModelForm):
    application = forms.ChoiceField(
        label="",
        choices=NimbusExperiment.Application.choices,
        widget=forms.widgets.Select(
            attrs={
                "class": "form-select",
            },
        ),
        initial="firefox-desktop",
    )
    feature_configs = forms.ChoiceField(
        label="",
        choices=[],
        widget=SingleSelectWidget(),
    )
    update_on_change_fields = ("application", "feature_configs")

    def get_feature_config_choices(self, application, qs):
        return sorted(
            [
                (application.pk, f"{application.name} - {application.description}")
                for application in NimbusFeatureConfig.objects.all()
                if application in qs
            ],
            key=lambda choice: choice[1].lower(),
        )

    class Meta:
        model = NimbusFeatureConfig
        fields = ["application", "feature_configs"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        selected_app = self.data.get("application") or self.get_initial_for_field(
            self.fields["application"], "application"
        )
        features = NimbusFeatureConfig.objects.filter(application=selected_app).order_by(
            "slug"
        )
        self.fields["feature_configs"].choices = self.get_feature_config_choices(
            selected_app, features
        )

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
