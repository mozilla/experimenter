from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

import markus
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusAlert,
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
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.slack.constants import SlackConstants
from experimenter.slack.tasks import (
    add_emoji_to_message_async,
    nimbus_send_slack_notification,
    remove_emoji_from_message_async,
)
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


class SlackNotificationMixin:
    slack_action = None

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        if self.slack_action:
            if experiment.enable_review_slack_notifications:
                action_text = SlackConstants.SLACK_FORM_ACTIONS[self.slack_action]

                # Call synchronously to get message timestamp and channel ID
                result = nimbus_send_slack_notification(
                    experiment_id=experiment.id,
                    email_addresses=experiment.notification_emails,
                    action_text=action_text,
                    requesting_user_email=self.request.user.email,
                    link_url=experiment.experiment_url,
                )
                if result:
                    message_ts, channel_id = result
                    alert_type = SlackConstants.SLACK_ACTION_TO_ALERT_TYPE[
                        self.slack_action
                    ]
                    NimbusAlert.objects.create(
                        experiment=experiment,
                        alert_type=alert_type,
                        message=action_text,
                        slack_thread_id=message_ts,
                        slack_channel_id=channel_id,
                    )
                    add_emoji_to_message_async.delay(
                        experiment.id,
                        alert_type,
                        SlackConstants.EmojiReaction.PENDING,
                    )
                    if (
                        experiment.kinto_collection
                        == settings.KINTO_COLLECTION_NIMBUS_SECURE
                    ):
                        add_emoji_to_message_async.delay(
                            experiment.id,
                            alert_type,
                            SlackConstants.EmojiReaction.SECURE,
                        )
        return experiment


class CancelRequestMixin:
    cancel_request_alert_type = None

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        if self.cancel_request_alert_type:
            remove_emoji_from_message_async.delay(
                experiment.id,
                self.cancel_request_alert_type,
                SlackConstants.EmojiReaction.PENDING,
            )
            add_emoji_to_message_async.delay(
                experiment.id,
                self.cancel_request_alert_type,
                SlackConstants.EmojiReaction.CANCEL,
            )
        return experiment


class NimbusDocumentationLinkForm(forms.ModelForm):
    title = forms.ChoiceField(
        choices=NimbusExperiment.DocumentationLink.choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    link = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Paste link here",
            }
        ),
    )

    class Meta:
        model = NimbusDocumentationLink
        fields = ("title", "link")

    def _get_validation_exclusions(self):
        return super()._get_validation_exclusions() | {"title", "link"}


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


RolloutBranchFeatureValueFormSet = inlineformset_factory(
    NimbusBranch,
    NimbusBranchFeatureValue,
    form=RolloutBranchFeatureValueForm,
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
    is_localized = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
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
    exclude_locales = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    languages = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Language.objects.all().order_by("code"),
        widget=MultiSelectWidget(),
    )
    exclude_languages = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    countries = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Country.objects.all().order_by("code"),
        widget=MultiSelectWidget(),
    )
    exclude_countries = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
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
            "is_localized",
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

        self.fields["is_localized"].widget.attrs.update(
            {
                "hx-post": reverse(
                    "nimbus-ui-new-update-audience", kwargs={"slug": self.instance.slug}
                ),
                "hx-trigger": "change",
                "hx-select": "#rollout-audience-body",
                "hx-target": "#rollout-audience-body",
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
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    requires_restart = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = NimbusExperiment
        fields = (
            "feature_configs",
            "is_firefox_labs_opt_in",
            "firefox_labs_title",
            "firefox_labs_description",
            "firefox_labs_description_links",
            "firefox_labs_group",
            "requires_restart",
            "warn_feature_schema",
            "prevent_pref_conflicts",
        )
        widgets = {
            "warn_feature_schema": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "prevent_pref_conflicts": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

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
                        "nimbus-ui-new-upload-rollout-screenshot",
                        kwargs={"slug": self.instance.slug},
                    ),
                    "hx-trigger": "change",
                    "hx-select": "#rollout-rollout-features-body",
                    "hx-target": "#rollout-rollout-features-body",
                }
            )

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

        if firefox_labs := self.instance.application_config.firefox_labs:
            self.fields["firefox_labs_group"].choices = firefox_labs.group_choices

        self.was_labs_opt_in = self.instance.is_firefox_labs_opt_in

        self.fields["is_firefox_labs_opt_in"].widget.attrs.update(
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

    def get_branch_feature_values_data(self):
        # Add temporary formset rows so newly selected, unsaved features get JSON
        # editors during the HTMX preview before Save persists them.
        if not self.is_bound:
            return None

        data = self.data.copy()
        prefix = "branch-feature-value"
        total_forms_key = f"{prefix}-TOTAL_FORMS"
        total_forms = int(data[total_forms_key])

        for feature_config_id in self._get_new_feature_config_ids(
            data, prefix, total_forms
        ):
            data[f"{prefix}-{total_forms}-feature_config"] = feature_config_id
            data[f"{prefix}-{total_forms}-value"] = "{}"
            total_forms += 1

        data[total_forms_key] = str(total_forms)
        return data

    def _get_new_feature_config_ids(self, data, prefix, total_forms):
        selected_values = self.fields["feature_configs"].widget.value_from_datadict(
            data, self.files, "feature_configs"
        )
        selected = [
            int(feature_config_id)
            for feature_config_id in selected_values or []
            if feature_config_id
        ]
        submitted = {
            int(data[f"{prefix}-{index}-feature_config"])
            for index in range(total_forms)
            if data.get(f"{prefix}-{index}-feature_config")
        }
        return [
            feature_config_id
            for feature_config_id in selected
            if feature_config_id not in submitted
        ]

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

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("is_firefox_labs_opt_in"):
            cleaned_data["firefox_labs_title"] = ""
            cleaned_data["firefox_labs_description"] = ""
            cleaned_data["firefox_labs_description_links"] = "null"
            cleaned_data["firefox_labs_group"] = ""
            cleaned_data["requires_restart"] = False

        return cleaned_data

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
        widgets = RolloutFeaturesForm.Meta.widgets

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


class UpdateStatusForm(NimbusChangeLogFormMixin, forms.ModelForm):
    status = None
    status_next = None
    publish_status = None
    is_paused = None

    required_status = None
    required_status_next = None
    required_publish_status = None
    required_is_paused = None
    requires_valid_rollout_launch = False

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

        if not self.instance.is_rollout and NimbusConstants.Status.DISABLED in (
            *required_state,
            *current_state,
            self.status,
            self.status_next,
        ):
            raise forms.ValidationError(
                NimbusUIConstants.ERROR_INVALID_DISABLED_TRANSITION
            )

        if self.requires_valid_rollout_launch:
            from experimenter.experiments.api.v5.serializers import (
                NimbusRolloutReviewSerializer,
            )

            if self.instance.get_invalid_fields_errors(
                serializer_class=NimbusRolloutReviewSerializer
            ):
                raise forms.ValidationError(
                    NimbusUIConstants.ERROR_INVALID_ROLLOUT_LAUNCH
                )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        self.instance.status = self.status
        self.instance.status_next = self.status_next
        previous_publish_status = self.instance.publish_status
        self.instance.publish_status = self.publish_status

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


# Draft to Live transitions


class DraftReviewRolloutForm(SlackNotificationMixin, UpdateStatusForm):
    requires_valid_rollout_launch = True
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE

    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW

    slack_action = SlackConstants.SLACK_ACTION_LAUNCH_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested rollout launch without Preview"


class DraftReviewApproveRolloutForm(UpdateStatusForm):
    requires_valid_rollout_launch = True
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the review."

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.stage_rollout_phase_advance()
        experiment.allocate_bucket_range()
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        remove_emoji_from_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.LAUNCH_REQUEST,
            SlackConstants.EmojiReaction.PENDING,
        )
        add_emoji_to_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.LAUNCH_REQUEST,
            SlackConstants.EmojiReaction.APPROVE,
        )

        return experiment


class DraftReviewRejectForm(CancelRequestMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.DRAFT
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    cancel_request_alert_type = NimbusConstants.AlertType.LAUNCH_REQUEST

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


# Preview to Live transitions


class PreviewReviewRolloutForm(SlackNotificationMixin, UpdateStatusForm):
    requires_valid_rollout_launch = True
    required_status = NimbusExperiment.Status.PREVIEW
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE

    status = NimbusExperiment.Status.DRAFT
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW

    slack_action = SlackConstants.SLACK_ACTION_LAUNCH_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested rollout launch from Preview"


# Preview to Draft transitions


class DraftToPreviewRolloutForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.DRAFT
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE

    status = NimbusExperiment.Status.PREVIEW
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE

    def get_changelog_message(self):
        return f"{self.request.user} launched rollout to Preview"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.allocate_bucket_range()
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        return experiment


class PreviewToDraftRolloutForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.PREVIEW
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE

    status = NimbusExperiment.Status.DRAFT
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE

    def get_changelog_message(self):
        return f"{self.request.user} moved the rollout back to Draft"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)
        return experiment


# Phase advance transitions


class AdvancePhaseReviewRolloutForm(SlackNotificationMixin, UpdateStatusForm):
    requires_valid_rollout_launch = True
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    slack_action = SlackConstants.SLACK_ACTION_ADVANCE_ROLLOUT_PHASE_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested review to advance rollout phase"


class AdvancePhaseReviewApproveRolloutForm(UpdateStatusForm):
    requires_valid_rollout_launch = True
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the advance rollout phase review request"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.stage_rollout_phase_advance()
        experiment.allocate_bucket_range()
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        remove_emoji_from_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.UPDATE_REQUEST,
            SlackConstants.EmojiReaction.PENDING,
        )
        add_emoji_to_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.UPDATE_REQUEST,
            SlackConstants.EmojiReaction.APPROVE,
        )

        return experiment


class AdvancePhaseReviewRejectRolloutForm(CancelRequestMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.LIVE
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    cancel_request_alert_type = NimbusConstants.AlertType.UPDATE_REQUEST

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


# Live to disabled transitions


class LiveToDisabledReviewRolloutForm(SlackNotificationMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.DISABLED
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    slack_action = SlackConstants.SLACK_ACTION_DISABLE_ROLLOUT_REQUEST

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.is_rollout_with_phases:
            raise forms.ValidationError(
                NimbusUIConstants.ERROR_INVALID_PHASELESS_ROLLOUT_DISABLED_TRANSITION
            )
        return cleaned_data

    def get_changelog_message(self):
        return f"{self.request.user} requested review to disable rollout"


class LiveToDisabledReviewApproveRolloutForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.DISABLED
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.LIVE
    status_next = NimbusExperiment.Status.DISABLED
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the disable rollout review request"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        remove_emoji_from_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.END_EXPERIMENT_REQUEST,
            SlackConstants.EmojiReaction.PENDING,
        )
        add_emoji_to_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.END_EXPERIMENT_REQUEST,
            SlackConstants.EmojiReaction.APPROVE,
        )

        return experiment


class LiveToDisabledReviewRejectRolloutForm(CancelRequestMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.LIVE
    required_status_next = NimbusExperiment.Status.DISABLED
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.LIVE
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    cancel_request_alert_type = NimbusConstants.AlertType.END_EXPERIMENT_REQUEST

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


# Disabled to Live transitions


class DisabledToLiveReviewRolloutForm(SlackNotificationMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.DISABLED
    required_status_next = None
    required_publish_status = NimbusExperiment.PublishStatus.IDLE

    status = NimbusExperiment.Status.DISABLED
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.REVIEW
    slack_action = SlackConstants.SLACK_ACTION_REENABLE_ROLLOUT_REQUEST

    def get_changelog_message(self):
        return f"{self.request.user} requested review to re-enable rollout"


class DisabledToLiveDuplicatePhaseReviewRolloutForm(DisabledToLiveReviewRolloutForm):
    def get_changelog_message(self):
        return (
            f"{self.request.user} duplicated the final rollout phase and requested "
            "review to re-enable rollout"
        )

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.rollout_phase_id is None:
            raise forms.ValidationError(
                NimbusUIConstants.ERROR_ROLLOUT_REENABLE_REQUIRES_CURRENT_PHASE
            )
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        experiment = NimbusExperiment.objects.select_for_update().get(pk=self.instance.pk)
        self.instance = experiment
        if (
            experiment.rollout_phase_next_id is None
            and experiment.rollout_phase
            and experiment.rollout_phase == experiment.rollout_phases.last()
        ):
            experiment.rollout_phases.create(
                population_percent=experiment.rollout_phase.population_percent
            )
        return super().save(commit=commit)


class DisabledToLiveReviewApproveRolloutForm(UpdateStatusForm):
    required_status = NimbusExperiment.Status.DISABLED
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.DISABLED
    status_next = NimbusExperiment.Status.LIVE
    publish_status = NimbusExperiment.PublishStatus.APPROVED

    def get_changelog_message(self):
        return f"{self.request.user} approved the re-enable rollout review request"

    @transaction.atomic
    def save(self, commit=True):
        experiment = super().save(commit=commit)
        experiment.stage_rollout_phase_advance()
        experiment.allocate_bucket_range()
        nimbus_check_kinto_push_queue_by_collection.apply_async(
            countdown=5, args=[experiment.kinto_collection]
        )
        remove_emoji_from_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.LAUNCH_REQUEST,
            SlackConstants.EmojiReaction.PENDING,
        )
        add_emoji_to_message_async.delay(
            experiment.id,
            NimbusConstants.AlertType.LAUNCH_REQUEST,
            SlackConstants.EmojiReaction.APPROVE,
        )
        return experiment


class DisabledToLiveReviewRejectRolloutForm(CancelRequestMixin, UpdateStatusForm):
    required_status = NimbusExperiment.Status.DISABLED
    required_status_next = NimbusExperiment.Status.LIVE
    required_publish_status = NimbusExperiment.PublishStatus.REVIEW

    status = NimbusExperiment.Status.DISABLED
    status_next = None
    publish_status = NimbusExperiment.PublishStatus.IDLE
    cancel_request_alert_type = NimbusConstants.AlertType.LAUNCH_REQUEST

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
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = NimbusRolloutPhase
        fields = ("start_date", "end_date", "population_percent")


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

        annotated_phases = {
            phase.id: phase for phase in self.instance.annotated_rollout_phases()
        }
        self.locked_phase_ids = {
            phase_id
            for phase_id, phase in annotated_phases.items()
            if phase.card_status in NimbusUIConstants.RolloutPhaseStatus.LOCKED
        }
        not_started = NimbusUIConstants.RolloutPhaseStatus.NOT_STARTED
        for phase_form in self.rollout_phases.forms:
            phase = annotated_phases.get(phase_form.instance.pk)
            status = phase.card_status if phase else not_started
            phase_form.card_status = status
            phase_form.card_status_display = (
                phase.card_status_display
                if phase
                else NimbusUIConstants.ROLLOUT_PHASE_STATUS_DISPLAY[not_started]
            )
            phase_form.is_current = bool(phase and phase.is_current)
            phase_form.is_locked = phase_form.instance.pk in self.locked_phase_ids
            if status == NimbusUIConstants.RolloutPhaseStatus.COMPLETE:
                disabled_fields = NimbusUIConstants.ROLLOUT_PHASE_FIELDS
            elif status in NimbusUIConstants.RolloutPhaseStatus.CURRENT:
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
    def apply_plan(self):
        plan_name = self.data.get("rollout_plan")
        if plan_name and plan_name in self.plans:
            self.instance.rollout_phases.exclude(id__in=self.locked_phase_ids).delete()
            for population_percent in self.plans[plan_name]:
                self.instance.rollout_phases.create(
                    population_percent=Decimal(str(population_percent))
                )

    @transaction.atomic
    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)
        self.apply_plan()
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

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("template_name") and not self.rollout_phases.is_valid():
            self.add_error(
                "template_name", NimbusUIConstants.ERROR_ROLLOUT_PLAN_FIX_ERRORS
            )
        return cleaned_data

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

    def get_changelog_message(self):
        status = (
            "enabled"
            if self.cleaned_data.get("enable_review_slack_notifications")
            else "disabled"
        )
        return f"{self.request.user} {status} review Slack notifications"
