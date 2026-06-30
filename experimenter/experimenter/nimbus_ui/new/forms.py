from collections import defaultdict

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
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
    NimbusFeatureConfig,
    Tag,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
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

        feature_config = (
            self.instance.feature_config if self.instance.feature_config_id else None
        )

        if (
            feature_config
            and (schema := feature_config.schemas.filter(version=None).first())
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


class RolloutBranchFeatureValueForm(NimbusBranchFeatureValueForm):
    class Meta:
        model = NimbusBranchFeatureValue
        fields = ("feature_config", "value")
        widgets = {"feature_config": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if (
            self.is_bound
            and not self.instance.feature_config_id
            and (feature_config_id := self.data.get(f"{self.prefix}-feature_config"))
        ):
            self.instance.feature_config = NimbusFeatureConfig.objects.filter(
                id=feature_config_id
            ).first()

    def clean_feature_config(self):
        return self.cleaned_data.get("feature_config") or (
            self.instance.feature_config if self.instance.feature_config_id else None
        )


RolloutBranchFeatureValueFormSet = inlineformset_factory(
    NimbusBranch,
    NimbusBranchFeatureValue,
    form=RolloutBranchFeatureValueForm,
    extra=0,
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

    class Meta:
        model = NimbusExperiment
        fields = [
            "name",
            "hypothesis",
            "public_description",
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

        self.branch_feature_values = RolloutBranchFeatureValueFormSet(
            data=self.get_branch_feature_values_data(),
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

    def get_branch_feature_values_data(self):
        # Add temporary formset rows so newly selected, unsaved features get JSON
        # editors during the HTMX preview before Save persists them.
        if not self.is_bound:
            return None

        data = self.data.copy()
        prefix = "branch-feature-value"
        total_forms_key = "branch-feature-value-TOTAL_FORMS"
        total_forms = int(data[total_forms_key])

        selected_feature_config_values = (
            data.getlist("feature_configs")
            if hasattr(data, "getlist")
            else data.get("feature_configs", [])
        )
        selected_feature_config_ids = [
            int(feature_config_id)
            for feature_config_id in selected_feature_config_values
            if feature_config_id
        ]
        submitted_feature_config_ids = {
            int(feature_config_id)
            for index in range(total_forms)
            if (feature_config_id := data.get(f"{prefix}-{index}-feature_config"))
        }

        new_feature_config_ids = [
            feature_config_id
            for feature_config_id in selected_feature_config_ids
            if feature_config_id not in submitted_feature_config_ids
        ]

        for feature_config_id in new_feature_config_ids:
            data[f"{prefix}-{total_forms}-feature_config"] = feature_config_id
            data[f"{prefix}-{total_forms}-value"] = "{}"
            total_forms += 1

        data[total_forms_key] = str(total_forms)
        return data

    @property
    def errors(self):
        errors = super().errors
        if any(self.branch_feature_values.errors):
            errors["branch_feature_values"] = self.branch_feature_values.errors
        return errors

    def is_valid(self):
        return super().is_valid() and self.branch_feature_values.is_valid()

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.branch_feature_values.save()
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
