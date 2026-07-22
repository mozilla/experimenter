from collections import defaultdict
from decimal import Decimal

import markus
from django import forms
from django.contrib.auth.models import User
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
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
    NimbusRolloutPhase,
    NimbusRolloutPlanTemplate,
    Tag,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.nimbus_ui.forms import NimbusBranchScreenshotForm
from experimenter.targeting.constants import NimbusTargetingConfig

metrics = markus.get_metrics("experimenter.nimbus_ui_forms")


class SelectedFirstMixin:
    def optgroups(self, name, value, attrs=None):
        groups = super().optgroups(name, value, attrs)
        selected = [g for g in groups if any(o.get("selected") for o in g[1])]
        unselected = [g for g in groups if not any(o.get("selected") for o in g[1])]
        return [*selected, *unselected]


class InlineRadioSelect(forms.RadioSelect):
    template_name = "common/widgets/inline_radio.html"
    option_template_name = "common/widgets/inline_radio_option.html"


class MultiSelectWidget(SelectedFirstMixin, forms.SelectMultiple):
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


class NimbusChangeLogFormMixin:
    def __init__(self, *args, request: HttpRequest = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def get_changelog_message(self) -> str:
        raise NotImplementedError

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        generate_nimbus_changelog(
            experiment, self.request.user, self.get_changelog_message()
        )
        metrics.incr("changelog_form.save", tags=[f"form:{type(self).__name__}"])
        return experiment


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


class SingleSelectWidget(SelectedFirstMixin, forms.Select):
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


RolloutBranchFeatureValueFormSet = inlineformset_factory(
    NimbusBranch,
    NimbusBranchFeatureValue,
    form=NimbusBranchFeatureValueForm,
    extra=0,
)

RolloutScreenshotFormSet = inlineformset_factory(
    NimbusBranch,
    NimbusBranchScreenshot,
    form=NimbusBranchScreenshotForm,
    extra=0,
    can_delete=False,
)


class RolloutOverviewForm(NimbusChangeLogFormMixin, forms.ModelForm):
    name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    hypothesis = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control"})
    )
    public_description = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )
    application = forms.ChoiceField(
        disabled=True,
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
            "name",
            "hypothesis",
            "public_description",
            "application",
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
        return f"{self.request.user} updated rollouts overview"


class DocumentationLinkCreateForm(RolloutOverviewForm):
    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.instance.documentation_links.create()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} added a documentation link"


class DocumentationLinkDeleteForm(RolloutOverviewForm):
    link_id = forms.ModelChoiceField(queryset=NimbusDocumentationLink.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = [*RolloutOverviewForm.Meta.fields, "link_id"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        documentation_link = self.cleaned_data["link_id"]
        documentation_link.delete()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} deleted a documentation link"


class RolloutRisksForm(NimbusChangeLogFormMixin, forms.ModelForm):
    YES_NO_CHOICES = (
        (True, "Yes"),
        (False, "No"),
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
    risk_ai = forms.TypedChoiceField(
        required=False,
        choices=YES_NO_CHOICES,
        widget=InlineRadioSelect,
        coerce=lambda x: x == "True",
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "risk_partner_related",
            "risk_revenue",
            "risk_brand",
            "risk_message",
            "risk_ai",
        ]

    def get_changelog_message(self):
        return f"{self.request.user} updated rollout risks"


class RolloutAudienceForm(NimbusChangeLogFormMixin, forms.ModelForm):
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

    YES_NO_CHOICES = (
        (True, "Yes"),
        (False, "No"),
    )
    localizations = forms.CharField(required=False, widget=forms.HiddenInput())
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
    is_sticky = forms.TypedChoiceField(
        required=False,
        choices=YES_NO_CHOICES,
        widget=InlineRadioSelect,
        coerce=lambda x: x == "True",
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
            "required_experiments_branches",
            "targeting_config_slug",
            "localizations",
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

    @transaction.atomic
    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        self.save_experiments_branches(
            "required_experiments_branches", NimbusExperimentBranchThroughRequired
        )
        self.save_experiments_branches(
            "excluded_experiments_branches", NimbusExperimentBranchThroughExcluded
        )
        return instance

    def get_changelog_message(self):
        return f"{self.request.user} updated audience"


class RolloutFeaturesForm(NimbusChangeLogFormMixin, forms.ModelForm):
    rollout_experience = forms.CharField(
        required=False,
        label="",
        widget=forms.widgets.Textarea(attrs={"class": "form-control"}),
    )
    feature_configs = FeatureConfigModelChoiceField(
        required=False,
        queryset=NimbusFeatureConfig.objects.all(),
        widget=FeatureConfigMultiSelectWidget(attrs={}),
    )

    class Meta:
        model = NimbusExperiment
        fields = ("feature_configs",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        screenshot_formset_args = {
            "data": self.data or None,
            "instance": self.reference_branch,
            "prefix": "rollout-screenshots",
        }
        if self.files:
            screenshot_formset_args["files"] = self.files
        self.rollout_screenshots = RolloutScreenshotFormSet(**screenshot_formset_args)

        for screenshot_form in self.rollout_screenshots.forms:
            screenshot_form.fields["image"].widget.attrs.update(
                {
                    "hx-post": reverse(
                        "nimbus-ui-new-update-rollout-features",
                        kwargs={"slug": self.instance.slug},
                    ),
                    "hx-trigger": "change",
                    "hx-select": "#rollout-rollout-features-body",
                    "hx-target": "#rollout-rollout-features-body",
                }
            )

        self.branch_feature_values = RolloutBranchFeatureValueFormSet(
            data=self.data or None,
            instance=self.reference_branch,
            prefix="branch-feature-value",
        )

        self.fields["feature_configs"].queryset = NimbusFeatureConfig.objects.filter(
            application=self.instance.application
        ).order_by("slug")

        self.fields["feature_configs"].widget.attrs.update(
            {
                "hx-post": reverse(
                    "nimbus-ui-new-update-rollout-features",
                    kwargs={"slug": self.instance.slug},
                ),
                "hx-trigger": "change",
                "hx-select": "#rollout-rollout-features-body",
                "hx-target": "#rollout-rollout-features-body",
            }
        )
        # We use the takeaways_summary to actually store the rollout experience since it
        # will remain unused as rollouts donot have results data
        self.fields["rollout_experience"].initial = self.instance.takeaways_summary

    @property
    def errors(self):
        errors = super().errors
        if any(self.branch_feature_values.errors):
            errors["branch_feature_values"] = self.branch_feature_values.errors
        if any(self.rollout_screenshots.errors):
            errors["rollout_screenshots"] = self.rollout_screenshots.errors
        return errors

    def is_valid(self):
        return (
            super().is_valid()
            and self.branch_feature_values.is_valid()
            and self.rollout_screenshots.is_valid()
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.branch_feature_values.save()
        self.rollout_screenshots.save()
        self.instance.takeaways_summary = self.cleaned_data.get("rollout_experience", "")

        experiment = super().save(*args, **kwargs)

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

        self.reference_branch.feature_values.filter(
            feature_config__in=deleted_feature_configs
        ).delete()

        for feature_config in new_feature_configs:
            self.reference_branch.feature_values.create(
                feature_config=feature_config, value="{}"
            )

        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} updated rollout features"

    @property
    def reference_branch(self):
        return self.instance.reference_branch or self.instance.branches.first()


class RolloutScreenshotCreateForm(RolloutFeaturesForm):
    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        self.reference_branch.screenshots.create()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} added a rollout screenshot"


class RolloutScreenshotDeleteForm(RolloutFeaturesForm):
    screenshot_id = forms.ModelChoiceField(queryset=NimbusBranchScreenshot.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = [
            "screenshot_id",
            *RolloutFeaturesForm.Meta.fields,
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        screenshot = self.cleaned_data["screenshot_id"]
        screenshot.delete()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} removed a rollout screenshot"


class RolloutQAStatusForm(NimbusChangeLogFormMixin, forms.ModelForm):
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
            "qa_comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Add QA comment or attach relevant links",
                }
            ),
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


class RolloutSignoffForm(NimbusChangeLogFormMixin, forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ["qa_signoff", "vp_signoff", "legal_signoff"]
        widgets = {
            "qa_signoff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "vp_signoff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "legal_signoff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def get_changelog_message(self):
        return f"{self.request.user} updated sign off"


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
        if self.instance and self.instance.pk:
            self.fields["collaborators"].initial = self.instance.subscribers.all()

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        if commit:
            experiment.subscribers.set(self.cleaned_data["collaborators"])
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} updated collaborators"


class RolloutPhaseForm(forms.ModelForm):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "From",
                "onfocus": "this.type='date'",
            }
        ),
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "To",
                "onfocus": "this.type='date'",
            }
        ),
    )
    population_percent = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100}),
    )

    class Meta:
        model = NimbusRolloutPhase
        fields = ("start_date", "end_date", "population_percent")

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if not self.fields["start_date"].disabled and bool(start_date) != bool(end_date):
            self.add_error(
                "end_date" if start_date else "start_date",
                NimbusUIConstants.ERROR_ROLLOUT_PHASE_DATE_INCOMPLETE,
            )
        elif start_date and end_date and end_date < start_date:
            self.add_error("end_date", NimbusUIConstants.ERROR_ROLLOUT_PHASE_DATE_ORDER)
        return cleaned_data


class RolloutScheduleForm(NimbusChangeLogFormMixin, forms.ModelForm):
    rollout_plan = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    template_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Name this rollout plan",
            }
        ),
    )
    rollout_advance_observations = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe observations here",
            }
        ),
    )
    rollout_pause_observations = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe observations here",
            }
        ),
    )

    class Meta:
        model = NimbusExperiment
        fields = ("rollout_advance_observations", "rollout_pause_observations")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.NimbusRolloutPhaseFormSet = inlineformset_factory(
            NimbusExperiment,
            NimbusRolloutPhase,
            form=RolloutPhaseForm,
            extra=0,
        )
        self.rollout_phases = self.NimbusRolloutPhaseFormSet(
            data=self.data or None,
            instance=self.instance,
        )
        self.plans = self.available_plans()
        self.fields["rollout_plan"].choices = [("", "None")] + [
            (name, f"{name} ({NimbusRolloutPlanTemplate.summary(phases)})")
            for name, phases in self.plans.items()
        ]
        self.fields["rollout_plan"].widget.attrs.update(
            {
                "hx-post": reverse(
                    "nimbus-ui-new-apply-rollout-plan",
                    kwargs={"slug": self.instance.slug},
                ),
                "hx-trigger": "change",
                "hx-target": "#rollout-schedule-body",
                "hx-swap": "outerHTML",
                "hx-include": "closest form",
            }
        )

        phase_statuses = {
            phase.id: phase.card_status
            for phase in self.instance.annotated_rollout_phases()
        }
        self.locked_phase_ids = {
            phase_id
            for phase_id, status in phase_statuses.items()
            if status
            in (
                NimbusUIConstants.RolloutPhaseStatus.COMPLETE,
                NimbusUIConstants.RolloutPhaseStatus.IN_PROGRESS,
            )
        }
        for phase_form in self.rollout_phases.forms:
            status = phase_statuses.get(phase_form.instance.pk)
            phase_form.is_locked = phase_form.instance.pk in self.locked_phase_ids
            if status == NimbusUIConstants.RolloutPhaseStatus.COMPLETE:
                disabled_fields = NimbusUIConstants.ROLLOUT_PHASE_FIELDS
            elif status == NimbusUIConstants.RolloutPhaseStatus.IN_PROGRESS:
                disabled_fields = ("population_percent",)
            else:
                disabled_fields = ()
            for field_name in disabled_fields:
                phase_form.fields[field_name].disabled = True

    @staticmethod
    def available_plans():
        plans = dict(NimbusUIConstants.ROLLOUT_TEMPLATE_PLANS)
        for template in NimbusRolloutPlanTemplate.objects.all():
            plans[template.name] = template.phases
        return plans

    def is_valid(self):
        return super().is_valid() and self.rollout_phases.is_valid()

    @transaction.atomic
    def save(self):
        experiment = super().save()
        self.rollout_phases.save()
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} updated rollout schedule"


class RolloutPhaseCreateForm(RolloutScheduleForm):
    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.instance.rollout_phases.create()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} added a rollout phase"


class RolloutPhaseDeleteForm(RolloutScheduleForm):
    phase_id = forms.ModelChoiceField(queryset=NimbusRolloutPhase.objects.all())

    class Meta:
        model = NimbusExperiment
        fields = ["phase_id"]

    def clean_phase_id(self):
        phase = self.cleaned_data["phase_id"]
        if phase.pk in self.locked_phase_ids:
            raise forms.ValidationError(NimbusUIConstants.ERROR_ROLLOUT_PHASE_LOCKED)
        return phase

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.cleaned_data["phase_id"].delete()
        return self.instance

    def get_changelog_message(self):
        return f"{self.request.user} removed a rollout phase"


class RolloutPlanApplyForm(RolloutScheduleForm):
    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        plan_name = self.cleaned_data.get("rollout_plan")
        if plan_name and plan_name in self.plans:
            experiment.rollout_phases.exclude(id__in=self.locked_phase_ids).delete()
            for population_percent in self.plans[plan_name]:
                experiment.rollout_phases.create(
                    population_percent=Decimal(str(population_percent))
                )
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} applied a rollout plan"


class RolloutPlanCreateForm(RolloutScheduleForm):
    def clean_template_name(self):
        name = (self.cleaned_data.get("template_name") or "").strip()
        if name and name in self.plans:
            raise forms.ValidationError(
                NimbusUIConstants.ERROR_ROLLOUT_PLAN_NAME_DUPLICATE
            )
        return name

    @transaction.atomic
    def save(self):
        experiment = super().save()
        name = self.cleaned_data.get("template_name")
        if name:
            phases = [
                float(phase.population_percent)
                for phase in experiment.rollout_phases.all()
            ]
            NimbusRolloutPlanTemplate.objects.create(name=name, phases=phases)
        return experiment

    def get_changelog_message(self):
        return f"{self.request.user} created a rollout plan template"


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
        widgets = {
            "enable_review_slack_notifications": forms.CheckboxInput(
                attrs={"class": "form-check-input m-0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.is_complete:
            self.fields["enable_review_slack_notifications"].widget.attrs["disabled"] = (
                True
            )

    def get_changelog_message(self):
        status = (
            "enabled"
            if self.cleaned_data.get("enable_review_slack_notifications")
            else "disabled"
        )
        return f"{self.request.user} {status} review Slack notifications"
