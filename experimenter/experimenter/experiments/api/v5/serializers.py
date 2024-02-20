import json
import logging
import re
import typing
from collections import defaultdict
from typing import Any, Optional

import jsonschema
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils.text import slugify
from rest_framework import serializers

from experimenter.base.models import (
    Country,
    Language,
    Locale,
    SiteFlag,
    SiteFlagNameChoices,
)
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
    NimbusFeatureVersion,
)
from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.outcomes import Outcomes
from experimenter.projects.models import Project

logger = logging.getLogger()


class TransitionConstants:
    VALID_STATUS_TRANSITIONS = {
        NimbusExperiment.Status.DRAFT: (NimbusExperiment.Status.PREVIEW,),
        NimbusExperiment.Status.PREVIEW: (NimbusExperiment.Status.DRAFT,),
    }

    # Valid status_next values for given status values in the
    # UI only. This does not represent the full list of
    # status_next values.
    VALID_STATUS_NEXT_VALUES = {
        NimbusExperiment.Status.DRAFT: (None, NimbusExperiment.Status.LIVE),
        NimbusExperiment.Status.PREVIEW: (None, NimbusExperiment.Status.LIVE),
        NimbusExperiment.Status.LIVE: (
            None,
            NimbusExperiment.Status.LIVE,
            NimbusExperiment.Status.COMPLETE,
        ),
    }

    # Valid publish_status transitions for given status
    # values in the UI only. This does not represent the
    # full list of publish_status transitions.
    VALID_PUBLISH_STATUS_TRANSITIONS = {
        NimbusExperiment.PublishStatus.IDLE: (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
        ),
        NimbusExperiment.PublishStatus.REVIEW: (
            NimbusExperiment.PublishStatus.IDLE,
            NimbusExperiment.PublishStatus.APPROVED,
        ),
    }

    STATUS_ALLOWS_UPDATE = {
        "all": [
            NimbusExperiment.Status.DRAFT,
        ],
        "experiments": [],
        "rollouts": [
            NimbusExperiment.Status.LIVE,
        ],
    }

    PUBLISH_STATUS_ALLOWS_UPDATE = {
        "all": [
            NimbusExperiment.PublishStatus.IDLE,
        ],
        "experiments": [],
        "rollouts": [],
    }

    STATUS_UPDATE_EXEMPT_FIELDS = {
        "all": [
            "is_archived",
            "publish_status",
            "qa_comment",
            "qa_status",
            "status_next",
            "status",
            "conclusion_recommendation",
            "subscribers",
            "takeaways_summary",
            "takeaways_metric_gain",
            "takeaways_qbr_learning",
            "takeaways_gain_amount",
        ],
        "experiments": [],
        "rollouts": ["population_percent"],
    }


class NestedRefResolver(jsonschema.RefResolver):
    """A custom ref resolver that handles bundled schema."""

    def __init__(self, schema):
        super().__init__(base_uri=None, referrer=None)

        if "$id" in schema:
            self.store[schema["$id"]] = schema

        if "$defs" in schema:
            for dfn in schema["$defs"].values():
                if "$id" in dfn:
                    self.store[dfn["$id"]] = dfn


_SerializerT = typing.TypeVar("_SerializerT", bound=serializers.ModelSerializer)


class ExperimentNameValidatorMixin(typing.Generic[_SerializerT]):
    instance: _SerializerT

    def validate_name(self, name):
        if not (self.instance or name):
            raise serializers.ValidationError("Name is required to create an experiment")

        if name:
            slug = slugify(name)

            if not slug:
                raise serializers.ValidationError(
                    "Name needs to contain alphanumeric characters"
                )

            if (
                self.instance is None
                and slug
                and NimbusExperiment.objects.filter(slug=slug).exists()
            ):
                raise serializers.ValidationError(
                    "Name maps to a pre-existing slug, please choose another name"
                )

        return name


class NimbusBranchScreenshotSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(max_length=1024, required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)

    class Meta:
        model = NimbusBranchScreenshot
        fields = (
            "id",
            "description",
            "image",
        )


class NimbusBranchFeatureValueListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        """Return a list of primitive data types representing the objects

        This enforces that the serialized data is ordered by the feature config ID.
        """
        iterable = data.all() if isinstance(data, models.Manager) else data

        return [
            self.child.to_representation(item)
            for item in iterable.order_by("feature_config__id")
        ]


class NimbusBranchFeatureValueSerializer(serializers.ModelSerializer):
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(), required=False, allow_null=False
    )
    value = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = NimbusBranchFeatureValue
        fields = (
            "feature_config",
            "value",
        )
        list_serializer_class = NimbusBranchFeatureValueListSerializer


class NimbusBranchSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    screenshots = NimbusBranchScreenshotSerializer(many=True, required=False)
    feature_values = NimbusBranchFeatureValueSerializer(many=True, required=False)

    class Meta:
        model = NimbusBranch
        fields = (
            "id",
            "name",
            "description",
            "ratio",
            "screenshots",
            "feature_values",
        )

    def validate_name(self, value):
        if slugify(value):
            return value
        else:
            raise serializers.ValidationError(
                "Name needs to contain alphanumeric characters."
            )

    def validate(self, data):
        data = super().validate(data)

        feature_values = data.get("feature_values")

        if feature_values is not None:
            unique_features = {fv["feature_config"] for fv in feature_values}
            if None not in unique_features and len(feature_values) != len(
                unique_features
            ):
                raise serializers.ValidationError(
                    {
                        "feature_values": [
                            {
                                "feature_config": (
                                    NimbusConstants.ERROR_DUPLICATE_BRANCH_FEATURE_VALUE
                                )
                            }
                            for _ in feature_values
                        ]
                    }
                )

        return data

    def _save_feature_values(self, feature_values, branch):
        branch.feature_values.all().delete()

        if feature_values is not None:
            for feature_value_data in feature_values:
                NimbusBranchFeatureValue.objects.create(
                    branch=branch, **feature_value_data
                )

    def _save_screenshots(self, screenshots, branch):
        if screenshots is None:
            return
        updated_screenshots = {x["id"]: x for x in screenshots if x.get("id")}
        for screenshot in branch.screenshots.all():
            screenshot_id = screenshot.id
            if screenshot_id not in updated_screenshots:
                screenshot.delete()
            else:
                serializer = NimbusBranchScreenshotSerializer(
                    screenshot,
                    data=updated_screenshots[screenshot_id],
                    partial=True,
                )
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

        new_screenshots = (x for x in screenshots if not x.get("id", None))
        for screenshot_data in new_screenshots:
            serializer = NimbusBranchScreenshotSerializer(
                data=screenshot_data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(branch=branch)

    def save(self, *args, **kwargs):
        feature_values = self.validated_data.pop("feature_values", None)
        screenshots = self.validated_data.pop("screenshots", None)
        slug = slugify(self.validated_data["name"])

        with transaction.atomic():
            branch = super().save(*args, slug=slug, **kwargs)

            self._save_feature_values(feature_values, branch)
            self._save_screenshots(screenshots, branch)

        return branch


class NimbusExperimentBranchMixin:
    def validate(self, data):
        data = super().validate(data)
        data = self._validate_duplicate_branch_names(data)
        data = self._validate_swapped_branch_names(data)
        return data

    def _validate_duplicate_branch_names(self, data):
        if "reference_branch" in data and "treatment_branches" in data:
            ref_branch_name = data["reference_branch"]["name"]
            treatment_branch_names = [b["name"] for b in data["treatment_branches"]]
            all_names = [ref_branch_name, *treatment_branch_names]
            if len(all_names) != len(set(all_names)):
                error = {"name": NimbusConstants.ERROR_DUPLICATE_BRANCH_NAME}
                raise serializers.ValidationError(
                    {
                        "reference_branch": error,
                        "treatment_branches": [error for _ in data["treatment_branches"]],
                    }
                )

        return data

    def _validate_swapped_branch_names(self, data):
        if "reference_branch" in data and "treatment_branches" in data:
            name_ids = defaultdict(set)

            for branch_data in data["treatment_branches"] + [data["reference_branch"]]:
                name_ids[branch_data["name"]].add(branch_data.get("id"))

            for branch in self.instance.branches.all():
                name_ids[branch.name].add(branch.id)

            swapped_branches = [name for (name, ids) in name_ids.items() if len(ids) > 1]

            if len(swapped_branches) > 1:
                raise serializers.ValidationError(
                    {
                        "reference_branch": {"name": NimbusConstants.ERROR_BRANCH_SWAP},
                        "treatment_branches": [
                            {"name": NimbusConstants.ERROR_BRANCH_SWAP}
                            for _ in data["treatment_branches"]
                        ],
                    }
                )

        return data

    def update(self, experiment, data):
        data.pop("reference_branch", None)
        data.pop("treatment_branches", None)

        branches_data = []

        if (
            reference_branch_data := self.initial_data.get("reference_branch")
        ) is not None:
            branches_data.append(reference_branch_data)

        if (
            treatment_branches_data := self.initial_data.get("treatment_branches")
        ) is not None:
            branches_data.extend(treatment_branches_data)

        with transaction.atomic():
            experiment = super().update(experiment, data)

            if {"reference_branch", "treatment_branches"}.intersection(
                set(self.initial_data.keys())
            ):
                saved_branch_ids = set(
                    experiment.branches.all().values_list("id", flat=True)
                )
                updated_branch_ids = {b["id"] for b in branches_data if b.get("id")}
                deleted_branch_ids = saved_branch_ids - updated_branch_ids
                for deleted_branch_id in deleted_branch_ids:
                    NimbusBranch.objects.get(id=deleted_branch_id).delete()

            for branch_data in branches_data:
                branch = None
                if branch_data.get("id") is not None:
                    branch = NimbusBranch.objects.get(id=branch_data["id"])

                serializer = NimbusBranchSerializer(
                    instance=branch,
                    data=branch_data,
                    partial=True,
                )
                if serializer.is_valid(raise_exception=True):
                    branch = serializer.save(experiment=experiment)

                    if branch_data == reference_branch_data:
                        experiment.reference_branch = branch
                        experiment.save()

        return experiment


class NimbusDocumentationLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusDocumentationLink
        fields = (
            "title",
            "link",
        )


class NimbusExperimentDocumentationLinkMixin:
    def update(self, experiment, data):
        documentation_links_data = data.pop("documentation_links", None)
        experiment = super().update(experiment, data)
        if documentation_links_data is not None:
            with transaction.atomic():
                experiment.documentation_links.all().delete()
                if documentation_links_data:
                    for link_data in documentation_links_data:
                        NimbusDocumentationLink.objects.create(
                            experiment=experiment, **link_data
                        )

        return experiment


class NimbusExperimentSubscriberSerializer(serializers.Serializer):
    email = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="email",
        required=True,
    )
    subscribed = serializers.BooleanField(required=True)


class NimbusExperimentSubscribersMixin:
    def update(self, experiment, data):
        subscribers = data.pop("subscribers", None)
        experiment = super().update(experiment, data)

        if self.instance and subscribers is not None:
            for subscriber in subscribers:
                if (
                    subscriber["subscribed"]
                    and subscriber["email"] not in self.instance.subscribers.all()
                ):
                    self.instance.subscribers.add(subscriber["email"])
                elif (
                    not subscriber["subscribed"]
                    and subscriber["email"] in self.instance.subscribers.all()
                ):
                    self.instance.subscribers.remove(subscriber["email"])

        return experiment


class NimbusStatusValidationMixin:
    """
    This will only validate certain statuses, and the validation does not
    cover status transitions made by Remote Settings.
    """

    def validate(self, data):
        data = super().validate(data)

        update_exempt_fields = TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS
        if self.instance:
            restrictive_statuses = set()
            exempt_fields = set()
            fields = ["all"]
            (
                fields.append("rollouts")
                if self.instance.is_rollout
                else fields.append("experiments")
            )

            restrictions = {
                "status": TransitionConstants.STATUS_ALLOWS_UPDATE,
                "publish_status": TransitionConstants.PUBLISH_STATUS_ALLOWS_UPDATE,
            }
            for f in fields:
                if update_exempt_fields[f] != []:
                    exempt_fields = exempt_fields.union(update_exempt_fields[f])
                for status in restrictions:
                    restrictive_statuses = restrictive_statuses.union(
                        restrictions[status][f]
                    )

            for status_field in restrictive_statuses:
                current_status = self.instance.status
                is_locked = current_status not in restrictive_statuses
                modifying_fields = set(data.keys()) - exempt_fields
                is_modifying_locked_fields = set(data.keys()).issubset(modifying_fields)

                if is_locked and is_modifying_locked_fields:
                    raise serializers.ValidationError(
                        {
                            "experiment": [
                                f"Nimbus Experiment has {status_field} "
                                f"'{current_status}', only "
                                f"{update_exempt_fields} "
                                f"can be changed, not: {modifying_fields}"
                            ]
                        }
                    )
            if (
                SiteFlag.objects.value(SiteFlagNameChoices.LAUNCHING_DISABLED)
                and self.instance.status == NimbusExperiment.Status.DRAFT
                and data.get("status_next") == NimbusExperiment.Status.LIVE
            ):
                raise serializers.ValidationError(
                    {"status_next": NimbusExperiment.ERROR_LAUNCHING_DISABLED}
                )

        return data


class NimbusStatusTransitionValidator:
    """
    This will only validate certain statuses, and the validation does not
    cover status transitions made by Remote Settings.
    """

    requires_context = True

    def __init__(self, transitions):
        self.transitions = transitions

    def __call__(self, value, serializer_field):
        """Validates using `VALID_STATUS_TRANSITIONS`"""

        field_name = serializer_field.source_attrs[-1]
        instance = getattr(serializer_field.parent, "instance", None)

        if instance and value:
            instance_value = getattr(instance, field_name)

            if value != instance_value and value not in self.transitions.get(
                instance_value, ()
            ):
                raise serializers.ValidationError(
                    f"Nimbus Experiment {field_name} cannot transition "
                    f"from {instance_value} to {value}."
                )


class NimbusExperimentBranchThroughSerializer(serializers.Serializer):
    branch_slug = serializers.CharField(min_length=0, max_length=1024, allow_null=True)

    def validate(self, data):
        data = super().validate(data)
        child_experiment = data[self.CHILD_FIELD]
        branch_slug = data["branch_slug"]

        if (
            branch_slug is not None
            and branch_slug
            not in child_experiment.branches.all().values_list("slug", flat=True)
        ):
            raise serializers.ValidationError(
                {
                    "branch_slug": (
                        f"{branch_slug} is not a valid branch "
                        f"for {child_experiment.name}: "
                        f"{[b.slug for b in child_experiment.branches.all()]}",
                    )
                }
            )

        return data


class NimbusExperimentBranchThroughRequiredSerializer(
    NimbusExperimentBranchThroughSerializer
):
    CHILD_FIELD = "required_experiment"

    required_experiment = serializers.PrimaryKeyRelatedField(
        queryset=NimbusExperiment.objects.all(),
    )


class NimbusExperimentBranchThroughExcludedSerializer(
    NimbusExperimentBranchThroughSerializer
):
    CHILD_FIELD = "excluded_experiment"

    excluded_experiment = serializers.PrimaryKeyRelatedField(
        queryset=NimbusExperiment.objects.all(),
    )


class NimbusExperimentSerializer(
    NimbusExperimentBranchMixin,
    NimbusStatusValidationMixin,
    NimbusExperimentDocumentationLinkMixin,
    NimbusExperimentSubscribersMixin,
    ExperimentNameValidatorMixin[NimbusExperiment],
    serializers.ModelSerializer,
):
    name = serializers.CharField(
        min_length=1, max_length=80, required=False, allow_blank=True
    )
    slug = serializers.ReadOnlyField()
    application = serializers.ChoiceField(
        choices=NimbusExperiment.Application.choices, required=False
    )
    channel = serializers.ChoiceField(
        choices=NimbusExperiment.Channel.choices, required=False
    )
    public_description = serializers.CharField(
        min_length=0, max_length=1024, required=False, allow_blank=True
    )
    is_enrollment_paused = serializers.BooleanField(source="is_paused", required=False)
    is_rollout_dirty = serializers.BooleanField(required=False)
    risk_mitigation_link = serializers.URLField(
        min_length=0, max_length=255, required=False, allow_blank=True
    )
    documentation_links = NimbusDocumentationLinkSerializer(many=True, required=False)
    hypothesis = serializers.CharField(
        min_length=0, max_length=1024, required=False, allow_blank=True
    )
    reference_branch = NimbusBranchSerializer(required=False)
    treatment_branches = NimbusBranchSerializer(many=True, required=False)
    prevent_pref_conflicts = serializers.BooleanField(required=False)
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    feature_configs = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        many=True,
        allow_null=True,
        required=False,
        write_only=True,
    )
    primary_outcomes = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    secondary_outcomes = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    population_percent = serializers.DecimalField(
        7, 4, min_value=0.0, max_value=100.0, required=False
    )
    status = serializers.ChoiceField(
        choices=NimbusExperiment.Status.choices,
        required=False,
        validators=[
            NimbusStatusTransitionValidator(
                transitions=TransitionConstants.VALID_STATUS_TRANSITIONS,
            )
        ],
    )
    publish_status = serializers.ChoiceField(
        choices=NimbusExperiment.PublishStatus.choices,
        required=False,
        validators=[
            NimbusStatusTransitionValidator(
                transitions=TransitionConstants.VALID_PUBLISH_STATUS_TRANSITIONS
            )
        ],
    )
    changelog_message = serializers.CharField(
        min_length=0, max_length=1024, required=True, allow_blank=False
    )
    countries = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        allow_null=True,
        required=False,
        many=True,
    )
    locales = serializers.PrimaryKeyRelatedField(
        queryset=Locale.objects.all(),
        allow_null=True,
        required=False,
        many=True,
    )
    languages = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(),
        allow_null=True,
        required=False,
        many=True,
    )
    projects = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        allow_null=True,
        required=False,
        many=True,
    )
    conclusion_recommendation = serializers.ChoiceField(
        choices=NimbusExperiment.ConclusionRecommendation.choices,
        allow_null=True,
        required=False,
    )
    takeaways_metric_gain = serializers.BooleanField(required=False)
    takeaways_qbr_learning = serializers.BooleanField(required=False)
    proposed_release_date = serializers.DateField(
        allow_null=True,
        required=False,
    )
    excluded_experiments_branches = NimbusExperimentBranchThroughExcludedSerializer(
        many=True,
        required=False,
    )
    required_experiments_branches = NimbusExperimentBranchThroughRequiredSerializer(
        many=True, required=False
    )
    qa_status = serializers.ChoiceField(
        choices=NimbusExperiment.QAStatus.choices,
        required=False,
    )
    qa_comment = serializers.CharField(
        min_length=0,
        max_length=4096,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    subscribers = serializers.ListField(
        child=NimbusExperimentSubscriberSerializer(),
        required=False,
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "application",
            "changelog_message",
            "channel",
            "conclusion_recommendation",
            "countries",
            "documentation_links",
            "excluded_experiments_branches",
            "feature_config",
            "feature_configs",
            "firefox_max_version",
            "firefox_min_version",
            "hypothesis",
            "is_archived",
            "is_enrollment_paused",
            "is_first_run",
            "is_localized",
            "is_rollout_dirty",
            "is_rollout",
            "is_sticky",
            "languages",
            "locales",
            "localizations",
            "name",
            "population_percent",
            "prevent_pref_conflicts",
            "primary_outcomes",
            "projects",
            "proposed_duration",
            "proposed_enrollment",
            "proposed_release_date",
            "public_description",
            "publish_status",
            "qa_comment",
            "qa_status",
            "reference_branch",
            "required_experiments_branches",
            "risk_brand",
            "risk_mitigation_link",
            "risk_partner_related",
            "risk_revenue",
            "secondary_outcomes",
            "slug",
            "status_next",
            "status",
            "subscribers",
            "takeaways_gain_amount",
            "takeaways_metric_gain",
            "takeaways_qbr_learning",
            "takeaways_summary",
            "targeting_config_slug",
            "total_enrolled_clients",
            "treatment_branches",
            "warn_feature_schema",
        ]

    def __init__(self, instance=None, data=None, **kwargs):
        self.is_draft_to_preview = instance and (
            instance.status == NimbusExperiment.Status.DRAFT
            and data
            and (data.get("status") == NimbusExperiment.Status.PREVIEW)
        )
        self.is_preview_to_draft = instance and (
            instance.status == NimbusExperiment.Status.PREVIEW
            and data
            and (data.get("status") == NimbusExperiment.Status.DRAFT)
        )
        self.should_call_preview_task = (
            self.is_draft_to_preview or self.is_preview_to_draft
        )
        self.should_call_push_task = (
            data and data.get("publish_status") == NimbusExperiment.PublishStatus.APPROVED
        )
        super().__init__(instance=instance, data=data, **kwargs)

    def validate_is_archived(self, is_archived):
        if self.instance.status not in (
            NimbusExperiment.Status.DRAFT,
            NimbusExperiment.Status.COMPLETE,
        ):
            raise serializers.ValidationError(
                f"An experiment in status {self.instance.status} can not be archived"
            )

        if self.instance.publish_status != NimbusExperiment.PublishStatus.IDLE:
            raise serializers.ValidationError(
                f"An experiment in publish status {self.instance.publish_status} "
                "can not be archived"
            )
        return is_archived

    def validate_publish_status(self, publish_status):
        """Validates using `VALID_PUBLISH_STATUS_TRANSITIONS`"""

        if publish_status == NimbusExperiment.PublishStatus.APPROVED and (
            self.instance.publish_status is not NimbusExperiment.PublishStatus.IDLE
            and not self.instance.can_review(self.context["user"])
        ):
            raise serializers.ValidationError(
                f'{self.context["user"]} can not review this experiment.'
            )
        return publish_status

    def validate_hypothesis(self, hypothesis):
        if hypothesis.strip() == NimbusExperiment.HYPOTHESIS_DEFAULT.strip():
            raise serializers.ValidationError(
                "Please describe the hypothesis of your experiment."
            )
        return hypothesis

    def validate_primary_outcomes(self, value):
        value_set = set(value)

        if len(value) > NimbusExperiment.MAX_PRIMARY_OUTCOMES:
            raise serializers.ValidationError(
                "Exceeded maximum primary outcome limit of "
                f"{NimbusExperiment.MAX_PRIMARY_OUTCOMES}."
            )

        valid_outcomes = {
            o.slug for o in Outcomes.by_application(self.instance.application)
        }

        if valid_outcomes.intersection(value_set) != value_set:
            invalid_outcomes = value_set - valid_outcomes
            raise serializers.ValidationError(
                f"Invalid choices for primary outcomes: {invalid_outcomes}"
            )

        return value

    def validate_secondary_outcomes(self, value):
        value_set = set(value)
        valid_outcomes = {
            o.slug for o in Outcomes.by_application(self.instance.application)
        }

        if valid_outcomes.intersection(value_set) != value_set:
            invalid_outcomes = value_set - valid_outcomes
            raise serializers.ValidationError(
                f"Invalid choices for secondary outcomes: {invalid_outcomes}"
            )

        return value

    def validate_status_next(self, value):
        """This validation for `status_next` does not cover any
        transitions made by Remote Settings."""

        valid_status_next = TransitionConstants.VALID_STATUS_NEXT_VALUES.get(
            self.instance.status, ()
        )
        if value not in valid_status_next:
            choices_str = ", ".join(str(choice) for choice in valid_status_next)
            raise serializers.ValidationError(
                f"Invalid choice for status_next: '{value}' - with status "
                f"'{self.instance.status}', the only valid choices are "
                f"'{choices_str}'"
            )

        return value

    def validate(self, data):
        data = super().validate(data)

        non_is_archived_fields = set(data.keys()) - set(
            NimbusExperiment.ARCHIVE_UPDATE_EXEMPT_FIELDS
        )
        if self.instance and self.instance.is_archived and non_is_archived_fields:
            raise serializers.ValidationError(
                {
                    field: f"{field} can't be updated while an experiment is archived"
                    for field in non_is_archived_fields
                }
            )

        primary_outcomes = set(data.get("primary_outcomes", []))
        secondary_outcomes = set(data.get("secondary_outcomes", []))
        if primary_outcomes.intersection(secondary_outcomes):
            raise serializers.ValidationError(
                {
                    "primary_outcomes": (
                        "Primary outcomes cannot overlap with secondary outcomes."
                    )
                }
            )

        if self.instance and "targeting_config_slug" in data:
            targeting_config_slug = data["targeting_config_slug"]
            application_choice = NimbusExperiment.Application(self.instance.application)
            targeting_config = NimbusExperiment.TARGETING_CONFIGS[targeting_config_slug]
            if application_choice.name not in targeting_config.application_choice_names:
                raise serializers.ValidationError(
                    {
                        "targeting_config_slug": (
                            f"Targeting config '{targeting_config.name}' is not "
                            f"available for application '{application_choice.label}'"
                        )
                    }
                )

        proposed_enrollment = data.get("proposed_enrollment")
        proposed_duration = data.get("proposed_duration")
        if (
            None not in (proposed_enrollment, proposed_duration)
            and proposed_enrollment > proposed_duration
        ):
            raise serializers.ValidationError(
                {
                    "proposed_enrollment": (
                        "The enrollment duration must be less than or "
                        "equal to the experiment duration."
                    )
                }
            )

        return data

    def update(self, experiment, validated_data):
        if (
            experiment.is_rollout
            and validated_data.get("population_percent") != experiment.population_percent
        ) and (
            not experiment.is_paused
            and experiment.status == NimbusExperiment.Status.LIVE
            and experiment.status_next is None
            and experiment.publish_status == NimbusExperiment.PublishStatus.IDLE
            and validated_data.get("publish_status")
            != NimbusConstants.PublishStatus.REVIEW
        ):
            # can be Live Update (Dirty), End Enrollment, or End Experiment
            # (including rejections) if we don't check validated_data
            validated_data["is_rollout_dirty"] = True

        self.changelog_message = validated_data.pop("changelog_message")
        return super().update(experiment, validated_data)

    def create(self, validated_data):
        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
                "owner": self.context["user"],
                "channel": next(
                    iter(
                        NimbusExperiment.APPLICATION_CONFIGS[
                            validated_data["application"]
                        ].channel_app_id.keys()
                    )
                ),
            }
        )
        self.changelog_message = validated_data.pop("changelog_message")
        return super().create(validated_data)

    def save_required_excluded_experiment_branches(self):
        required_experiment_branches = self.validated_data.pop(
            "required_experiments_branches", None
        )
        if required_experiment_branches is not None:
            NimbusExperimentBranchThroughRequired.objects.filter(
                parent_experiment=self.instance
            ).all().delete()
            for required_experiment_branch in required_experiment_branches:
                NimbusExperimentBranchThroughRequired.objects.create(
                    parent_experiment=self.instance,
                    child_experiment=required_experiment_branch["required_experiment"],
                    branch_slug=required_experiment_branch["branch_slug"],
                )

        excluded_experiment_branches = self.validated_data.pop(
            "excluded_experiments_branches", None
        )
        if excluded_experiment_branches is not None:
            NimbusExperimentBranchThroughExcluded.objects.filter(
                parent_experiment=self.instance
            ).all().delete()
            for excluded_experiment_branch in excluded_experiment_branches:
                NimbusExperimentBranchThroughExcluded.objects.create(
                    parent_experiment=self.instance,
                    child_experiment=excluded_experiment_branch["excluded_experiment"],
                    branch_slug=excluded_experiment_branch["branch_slug"],
                )

    def save(self):
        feature_configs_provided = "feature_configs" in self.validated_data
        feature_configs = self.validated_data.pop("feature_configs", None)

        with transaction.atomic():
            # feature_configs must be set before we call super to make sure
            # the feature_config is available when the branches save their
            # feature_values
            if self.instance:
                if feature_configs_provided:
                    self.instance.feature_configs.clear()

                if feature_configs:
                    self.instance.feature_configs.add(*feature_configs)

                if self.is_preview_to_draft:
                    self.instance.published_dto = None

            self.save_required_excluded_experiment_branches()

            experiment = super().save()

            if experiment.has_filter(experiment.Filters.SHOULD_ALLOCATE_BUCKETS):
                experiment.allocate_bucket_range()

            if self.should_call_preview_task:
                nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)

            if self.should_call_push_task:
                collection = experiment.application_config.kinto_collection
                nimbus_check_kinto_push_queue_by_collection.apply_async(
                    countdown=5, args=[collection]
                )

            generate_nimbus_changelog(
                experiment, self.context["user"], message=self.changelog_message
            )

            return experiment


class NimbusExperimentCsvSerializer(serializers.ModelSerializer):
    experiment_name = serializers.CharField(source="name")
    product_area = serializers.CharField(source="application")
    rollout = serializers.BooleanField(source="is_rollout")
    owner = serializers.SlugRelatedField(read_only=True, slug_field="email")
    feature_configs = serializers.SerializerMethodField()
    experiment_summary = serializers.CharField(source="experiment_url")
    results_url = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = [
            "launch_month",
            "product_area",
            "experiment_name",
            "owner",
            "feature_configs",
            "start_date",
            "enrollment_duration",
            "end_date",
            "results_url",
            "experiment_summary",
            "rollout",
            "hypothesis",
        ]

    def get_feature_configs(self, obj):
        sorted_features = sorted(
            obj.feature_configs.all(), key=lambda feature: feature.name
        )
        return ",".join([feature.name for feature in sorted_features])

    def get_results_url(self, obj):
        return f"{obj.experiment_url}results" if obj.results_ready else ""


class NimbusBranchScreenshotReviewSerializer(NimbusBranchScreenshotSerializer):
    # Round-trip serialization & validation for review can use a string path
    image = serializers.CharField(required=True)
    description = serializers.CharField(required=True)


class NimbusBranchFeatureValueReviewSerializer(NimbusBranchFeatureValueSerializer):
    id = serializers.IntegerField()
    value = serializers.CharField(allow_blank=False)

    class Meta:
        model = NimbusBranchFeatureValue
        fields = (
            "id",
            "branch",
            "feature_config",
            "value",
        )
        list_serializer_class = NimbusBranchFeatureValueListSerializer

    def validate_value(self, value):
        data = None
        if value:
            try:
                data = json.loads(value)
            except Exception as e:
                raise serializers.ValidationError(f"Invalid JSON: {e.msg}") from e

        def throw_on_float(item):
            if isinstance(item, (list, tuple)):
                for i in item:
                    throw_on_float(i)
            elif isinstance(item, dict):
                for i in item.values():
                    throw_on_float(i)
            elif isinstance(item, float):
                raise serializers.ValidationError(
                    NimbusExperiment.ERROR_NO_FLOATS_IN_FEATURE_VALUE
                )

        if data is not None:
            throw_on_float(data)

        return value


class NimbusBranchReviewSerializer(NimbusBranchSerializer):
    feature_values = NimbusBranchFeatureValueReviewSerializer(many=True, required=True)
    screenshots = NimbusBranchScreenshotReviewSerializer(many=True, required=False)


class NimbusReviewSerializer(serializers.ModelSerializer):
    public_description = serializers.CharField(required=True)
    proposed_duration = serializers.IntegerField(required=True, min_value=1)
    proposed_enrollment = serializers.IntegerField(required=True, min_value=1)
    population_percent = serializers.DecimalField(
        7,
        4,
        min_value=0.00009,
        max_value=100.0,
        required=True,
        error_messages={"min_value": NimbusConstants.ERROR_POPULATION_PERCENT_MIN},
    )
    total_enrolled_clients = serializers.IntegerField(required=True, min_value=1)
    firefox_min_version = serializers.ChoiceField(
        NimbusExperiment.Version.choices, required=True
    )
    application = serializers.ChoiceField(
        NimbusExperiment.Application.choices, required=True
    )
    hypothesis = serializers.CharField(required=True)
    documentation_links = NimbusDocumentationLinkSerializer(many=True)
    targeting_config_slug = serializers.ChoiceField(
        NimbusExperiment.TargetingConfig.choices, required=True
    )
    reference_branch = NimbusBranchReviewSerializer(required=True)
    treatment_branches = NimbusBranchReviewSerializer(many=True)
    feature_configs = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        many=True,
        allow_empty=False,
        error_messages={"empty": NimbusConstants.ERROR_REQUIRED_FEATURE_CONFIG},
    )
    primary_outcomes = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    secondary_outcomes = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    risk_partner_related = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"null": NimbusConstants.ERROR_REQUIRED_QUESTION},
    )
    risk_revenue = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"null": NimbusConstants.ERROR_REQUIRED_QUESTION},
    )
    risk_brand = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"null": NimbusConstants.ERROR_REQUIRED_QUESTION},
    )
    is_localized = serializers.BooleanField(required=False)
    localizations = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    excluded_experiments = serializers.PrimaryKeyRelatedField(
        queryset=NimbusExperiment.objects.all(),
        many=True,
        allow_empty=True,
    )
    required_experiments = serializers.PrimaryKeyRelatedField(
        queryset=NimbusExperiment.objects.all(),
        many=True,
        allow_empty=True,
    )

    class Meta:
        model = NimbusExperiment
        exclude = ("id",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = defaultdict(list)

        self.schemas_by_feature_id: dict[
            str, NimbusFeatureConfig.VersionedSchemaRange
        ] = {}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["feature_config"] = None
        if instance.feature_configs.exists():
            data["feature_config"] = (
                instance.feature_configs.all().order_by("slug").first().id
            )
        return data

    def validate_reference_branch(self, value):
        if value["description"] == "":
            raise serializers.ValidationError(
                {"description": [NimbusConstants.ERROR_REQUIRED_FIELD]}
            )
        return value

    def validate_treatment_branches(self, value):
        errors = []

        for branch in value:
            error = {}
            if self.instance and self.instance.is_rollout:
                error["name"] = [NimbusConstants.ERROR_SINGLE_BRANCH_FOR_ROLLOUT]
            if branch["description"] == "":
                error["description"] = [NimbusConstants.ERROR_REQUIRED_FIELD]
            errors.append(error)

        if any(errors):
            raise serializers.ValidationError(errors)
        return value

    def validate_hypothesis(self, value):
        if value == NimbusExperiment.HYPOTHESIS_DEFAULT.strip():
            raise serializers.ValidationError("Hypothesis cannot be the default value.")
        return value

    def validate_excluded_experiments(self, value):
        return self._validate_required_or_excluded_experiments(value)

    def validate_required_experiments(self, value):
        return self._validate_required_or_excluded_experiments(value)

    def validate_feature_configs(self, value):
        if len(value) > NimbusExperiment.MULTIFEATURE_MAX_FEATURES:
            raise serializers.ValidationError(
                NimbusExperiment.ERROR_MULTIFEATURE_TOO_MANY_FEATURES
            )
        return value

    def _validate_required_or_excluded_experiments(self, value):
        if self.instance and value:
            if self.instance in value:
                raise serializers.ValidationError(
                    [NimbusExperiment.ERROR_EXCLUDED_REQUIRED_INCLUDES_SELF]
                )

            for experiment in value:
                if experiment.application != self.instance.application:
                    raise serializers.ValidationError(
                        [
                            NimbusExperiment.ERROR_EXCLUDED_REQUIRED_DIFFERENT_APPLICATION.format(
                                slug=experiment.slug
                            )
                        ]
                    )

        return value

    def _validate_feature_value(
        self,
        application: str,
        feature_config: NimbusFeatureConfig,
        value: str,
        schemas_in_range: NimbusFeatureConfig.VersionedSchemaRange,
        localizations: Optional[dict[str, Any]],
        channel: str,
    ) -> list[str]:
        if schemas_in_range.unsupported_in_range:
            return [
                NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_RANGE.format(
                    feature_config=feature_config,
                )
            ]

        errors = []
        for version in schemas_in_range.unsupported_versions:
            errors.append(
                NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_VERSION.format(
                    feature_config=feature_config,
                    version=version,
                )
            )

        if application == NimbusExperiment.Application.DESKTOP:
            errors.extend(
                self._validate_feature_value_with_schema(
                    schemas_in_range,
                    value,
                    localizations,
                )
            )
        else:
            errors.extend(
                self._validate_feature_value_with_fml(
                    schemas_in_range,
                    NimbusFmlLoader.create_loader(application, channel),
                    feature_config,
                    value,
                )
            )

        return errors

    def _validate_feature_value_with_schema(
        self,
        schemas_in_range: NimbusFeatureConfig.VersionedSchemaRange,
        value: str,
        localizations: Optional[dict[str, Any]],
    ) -> list[str]:
        errors = []

        json_value = json.loads(value)
        for schema in schemas_in_range.schemas:
            if schema.schema is None:  # Only in tests.
                continue

            json_schema = json.loads(schema.schema)
            if not localizations:
                errors.extend(
                    self._validate_schema(json_value, json_schema, schema.version)
                )
            else:
                for locale_code, substitutions in localizations.items():
                    try:
                        substituted_value = self._substitute_localizations(
                            json_value, substitutions, locale_code
                        )
                    except LocalizationError as e:
                        errors.append(str(e))
                        continue

                    if schema_errors := self._validate_schema(
                        substituted_value, json_schema, schema.version
                    ):
                        err_msg = (
                            f"Schema validation errors occured during locale "
                            f"substitution for locale {locale_code}"
                        )

                        if schema.version is not None:
                            err_msg += f" at version {schema.version}"

                        errors.append(err_msg)
                        errors.extend(schema_errors)

        return errors

    def _validate_feature_value_with_fml(
        self,
        schemas_in_range: NimbusFeatureConfig.VersionedSchemaRange,
        loader: NimbusFmlLoader,
        feature_config: NimbusFeatureConfig,
        blob: str,
    ) -> list[str]:
        errors = []
        for schema in schemas_in_range.schemas:
            version = schema.version
            if fml_errors := loader.get_fml_errors(blob, feature_config.slug, version):
                errors.extend(
                    [
                        f"{NimbusExperiment.ERROR_FML_VALIDATION}: {e.message} at line "
                        f"{e.line+1} column {e.col} at version {version}"
                        for e in fml_errors
                    ]
                )

        return errors

    def _validate_schema(
        self, obj: Any, schema: dict[str, Any], version: Optional[NimbusFeatureVersion]
    ) -> list[str]:
        try:
            jsonschema.validate(obj, schema, resolver=NestedRefResolver(schema))
        except jsonschema.ValidationError as e:
            err_msg = e.message
            if version is not None:
                err_msg += f" at version {version}"

            return [err_msg]

        return []

    def _validate_feature_configs(self, data):
        application = data.get("application")
        feature_configs = data.get("feature_configs", [])

        min_version = None
        max_version = None
        if not NimbusExperiment.Application.is_web(application):
            raw_min_version = data.get("firefox_min_version", "")
            raw_max_version = data.get("firefox_max_version", "")

            # We've already validated the versions in _validate_versions.
            min_version = NimbusExperiment.Version.parse(raw_min_version)
            if raw_max_version:
                max_version = NimbusExperiment.Version.parse(raw_max_version)

        warn_feature_schema = data.get("warn_feature_schema", False)

        errors = {
            "feature_configs": [
                f"Feature Config application {feature_config.application} "
                f"does not match experiment application "
                f"{self.instance.application}."
            ]
            for feature_config in feature_configs
            if self.instance.application != feature_config.application
        }
        if data.get("is_localized"):
            localizations = json.loads(data.get("localizations"))
        else:
            localizations = None

        application = data.get("application")
        channel = data.get("channel")

        reference_branch_errors = []

        for feature_value_data in data.get("reference_branch", {}).get(
            "feature_values", []
        ):
            # Cache the versioned schema range for each feature so we can re-use
            # them in the treatment branch validation below without performing
            # the queries again.
            feature_config: NimbusFeatureConfig = feature_value_data["feature_config"]
            self.schemas_by_feature_id[
                feature_config.id
            ] = feature_config.get_versioned_schema_range(min_version, max_version)

            if feature_errors := self._validate_feature_value(
                application,
                feature_config,
                feature_value_data["value"],
                self.schemas_by_feature_id[feature_config.id],
                localizations,
                channel,
            ):
                reference_branch_errors.append({"value": feature_errors})
            else:
                reference_branch_errors.append({})

        if any(reference_branch_errors):
            errors["reference_branch"] = {"feature_values": reference_branch_errors}

        treatment_branches_errors = []
        treatment_branches_errors_found = False
        for treatment_branch_data in data.get("treatment_branches", []):
            treatment_branch_errors = []

            for feature_value_data in treatment_branch_data["feature_values"]:
                feature_config: NimbusFeatureConfig = feature_value_data["feature_config"]

                if feature_errors := self._validate_feature_value(
                    application,
                    feature_config,
                    feature_value_data["value"],
                    self.schemas_by_feature_id[feature_config.id],
                    localizations,
                    channel,
                ):
                    treatment_branch_errors.append({"value": feature_errors})
                    treatment_branches_errors_found = True
                else:
                    treatment_branch_errors.append({})

            treatment_branches_errors.append({"feature_values": treatment_branch_errors})

        if treatment_branches_errors_found:
            errors["treatment_branches"] = treatment_branches_errors

        if any(errors):
            if warn_feature_schema:
                self.warnings = errors
            else:
                raise serializers.ValidationError(errors)

        return data

    def _validate_versions(self, data):
        min_version = data.get("firefox_min_version", "")
        max_version = data.get("firefox_max_version", "")
        is_rollout = data.get("is_rollout")
        application = data.get("application")

        if NimbusExperiment.Application.is_web(application):
            return data

        if min_version == "":
            raise serializers.ValidationError(
                {
                    "firefox_min_version": [
                        NimbusExperiment.ERROR_FIREFOX_VERSION_MIN_96
                    ],
                }
            )

        parsed_min_version = NimbusExperiment.Version.parse(min_version)

        if parsed_min_version < NimbusExperiment.Version.parse(
            NimbusExperiment.MIN_REQUIRED_VERSION
        ):
            raise serializers.ValidationError(
                {
                    "firefox_min_version": [
                        NimbusExperiment.ERROR_FIREFOX_VERSION_MIN_96
                    ],
                }
            )

        if rollout_live_resize_min_app_version := (
            NimbusConstants.ROLLOUT_LIVE_RESIZE_MIN_SUPPORTED_VERSION.get(application)
        ):
            parsed_min_app_version = NimbusExperiment.Version.parse(
                rollout_live_resize_min_app_version
            )
            if is_rollout and parsed_min_version < parsed_min_app_version:
                self.warnings["firefox_min_version"] = [
                    NimbusConstants.ERROR_ROLLOUT_VERSION.format(
                        application=NimbusExperiment.Application(application).label,
                        version=parsed_min_app_version,
                    )
                ]

        excluded_experiments = data.get("excluded_experiments")
        required_experiments = data.get("required_experiments")
        if (excluded_experiments or required_experiments) and (
            parsed_min_version
            < NimbusExperiment.Version.parse(
                NimbusExperiment.EXCLUDED_REQUIRED_MIN_VERSION
            )
        ):
            raise serializers.ValidationError(
                {
                    "firefox_min_version": [
                        NimbusExperiment.ERROR_EXCLUDED_REQUIRED_MIN_VERSION,
                    ],
                }
            )

        if (
            min_version != ""
            and max_version != ""
            and (parsed_min_version > NimbusExperiment.Version.parse(max_version))
        ):
            raise serializers.ValidationError(
                {
                    "firefox_min_version": [NimbusExperiment.ERROR_FIREFOX_VERSION_MIN],
                    "firefox_max_version": [NimbusExperiment.ERROR_FIREFOX_VERSION_MAX],
                }
            )
        return data

    def _validate_languages_versions(self, data):
        application = data.get("application")
        min_version = data.get("firefox_min_version", "")

        if data.get("languages", []):
            min_supported_version = (
                NimbusConstants.LANGUAGES_APPLICATION_SUPPORTED_VERSION[application]
            )
            if NimbusExperiment.Version.parse(
                min_version
            ) < NimbusExperiment.Version.parse(min_supported_version):
                raise serializers.ValidationError(
                    {
                        "languages": f"Language targeting is not \
                            supported for this application below \
                                version {min_supported_version}"
                    }
                )
        return data

    def _validate_countries_versions(self, data):
        application = data.get("application")
        min_version = data.get("firefox_min_version", "")

        if data.get("countries", []):
            min_supported_version = (
                NimbusConstants.COUNTRIES_APPLICATION_SUPPORTED_VERSION[application]
            )
            if NimbusExperiment.Version.parse(
                min_version
            ) < NimbusExperiment.Version.parse(min_supported_version):
                raise serializers.ValidationError(
                    {
                        "countries": f"Country targeting is \
                            not supported for this application \
                                below version {min_supported_version}"
                    }
                )
        return data

    def _validate_enrollment_targeting(self, data):
        excluded_experiments = set(data.get("excluded_experiments", []))
        required_experiments = set(data.get("required_experiments", []))

        if excluded_experiments & required_experiments:
            raise serializers.ValidationError(
                {
                    "excluded_experiments": [
                        NimbusExperiment.ERROR_EXCLUDED_REQUIRED_MUTUALLY_EXCLUSIVE,
                    ],
                    "required_experiments": [
                        NimbusExperiment.ERROR_EXCLUDED_REQUIRED_MUTUALLY_EXCLUSIVE,
                    ],
                }
            )

        return data

    def _validate_sticky_enrollment(self, data):
        targeting_config_slug = data.get("targeting_config_slug")
        targeting_config = NimbusExperiment.TARGETING_CONFIGS[targeting_config_slug]
        is_sticky = data.get("is_sticky")
        sticky_required = targeting_config.sticky_required
        if sticky_required and (not is_sticky):
            raise serializers.ValidationError(
                {
                    "is_sticky": "Selected targeting expression requires sticky\
                    enrollment to function correctly"
                }
            )

        return data

    def _validate_rollout_version_support(self, data):
        if not self.instance or not self.instance.is_rollout:
            return data

        min_version = NimbusExperiment.Version.parse(self.instance.firefox_min_version)
        rollout_version_supported = NimbusExperiment.ROLLOUT_SUPPORT_VERSION.get(
            self.instance.application
        )
        if (
            rollout_version_supported is not None
            and min_version < NimbusExperiment.Version.parse(rollout_version_supported)
        ):
            raise serializers.ValidationError(
                {
                    "is_rollout": f"Rollouts are not supported for this application \
                                below version {rollout_version_supported}"
                }
            )

        return data

    def _validate_bucket_duplicates(self, data):
        is_rollout = self.instance.is_rollout
        if not self.instance or not is_rollout:
            return data

        count = NimbusExperiment.objects.filter(
            status=NimbusExperiment.Status.LIVE,
            channel=self.instance.channel,
            application=self.instance.application,
            targeting_config_slug=self.instance.targeting_config_slug,
            feature_configs__in=self.instance.feature_configs.all(),
            is_rollout=is_rollout,
        ).count()

        if count > 0:
            self.warnings["bucketing"] = [NimbusConstants.ERROR_BUCKET_EXISTS]

        return data

    def _validate_localizations(self, data):
        is_localized = data.get("is_localized")
        if not is_localized:
            return data

        application = data.get("application")
        if application != NimbusExperiment.Application.DESKTOP:
            raise serializers.ValidationError(
                {
                    "application": [
                        "Localized experiments are only supported for Firefox Desktop."
                    ]
                }
            )

        min_version = data.get("firefox_min_version", "")
        supported_version = NimbusExperiment.Version.parse(
            NimbusConstants.LOCALIZATION_SUPPORTED_VERSION[application]
        )
        if min_version == "" or (
            NimbusExperiment.Version.parse(min_version) < supported_version
        ):
            raise serializers.ValidationError(
                {
                    "firefox_min_version": [
                        NimbusConstants.ERROR_DESKTOP_LOCALIZATION_VERSION,
                    ],
                }
            )

        experiment_locales = data.get("locales")
        if not experiment_locales:
            raise serializers.ValidationError(
                {"locales": ["Locales must not be empty for a localized experiment."]}
            )

        localizations_json = data.get("localizations")
        try:
            localizations = json.loads(localizations_json)
        except json.decoder.JSONDecodeError as e:
            raise serializers.ValidationError(
                {"localizations": [f"Invalid JSON: {e}"]}
            ) from e

        schema = settings.EXPERIMENT_SCHEMA["definitions"]["NimbusExperiment"][
            "properties"
        ]["localizations"]

        try:
            jsonschema.validate(localizations, schema)
        except Exception as e:
            raise serializers.ValidationError(
                {"localizations": [f"Localization schema validation error: {e}"]}
            ) from e

        experiment_locale_codes = [locale.code for locale in experiment_locales]
        for locale_code in experiment_locale_codes:
            if locale_code not in localizations:
                raise serializers.ValidationError(
                    {
                        "localizations": [
                            f"Experiment locale {locale_code} not present in "
                            f"localizations."
                        ]
                    }
                )

        for localization in localizations:
            if localization not in experiment_locale_codes:
                raise serializers.ValidationError(
                    {
                        "localizations": [
                            f"Localization locale {localization} does not exist in "
                            f"experiment locales."
                        ]
                    }
                )

        return data

    @staticmethod
    def _substitute_localizations(feature_value, substitutions, locale_code):
        ID_RE = re.compile(r"^[A-Za-z0-9\-]+$")
        missing_ids = set()

        def substitute(value):
            if isinstance(value, list):
                return [substitute(item) for item in value]

            if isinstance(value, dict):
                if "$l10n" in value and isinstance(value["$l10n"], dict):
                    l10n = value["$l10n"]

                    if not isinstance(l10n.get("id"), str):
                        raise LocalizationError("$l10n object is missing 'id'")

                    sub_id = value["$l10n"]["id"]

                    if len(sub_id) < NimbusConstants.L10N_MIN_STRING_ID_LEN:
                        raise LocalizationError(
                            f"$l10n id '{sub_id}' must be at least "
                            f"{NimbusConstants.L10N_MIN_STRING_ID_LEN} characters long"
                        )

                    if ID_RE.match(sub_id) is None:
                        raise LocalizationError(
                            f"$l10n id '{sub_id}' contains invalid characters; only "
                            f"alphanumeric characters and dashes are permitted"
                        )

                    if not isinstance(l10n.get("text"), str):
                        raise LocalizationError(
                            f"$l10n object with id '{sub_id}' is missing 'text'"
                        )

                    if not isinstance(l10n.get("comment"), str):
                        raise LocalizationError(
                            f"$l10n object with id '{sub_id}' is missing 'comment'"
                        )

                    if sub_id not in substitutions:
                        missing_ids.add(sub_id)
                        return None

                    return substitutions[sub_id]
                else:
                    return {k: substitute(v) for k, v in value.items()}

            return value

        subbed = substitute(feature_value)

        if missing_ids:
            missing_ids_str = ", ".join(sorted(missing_ids))
            raise serializers.ValidationError(
                {
                    "localizations": [
                        f"Locale {locale_code} is missing substitutions for IDs: "
                        f"{missing_ids_str}"
                    ]
                }
            )

        return subbed

    def _validate_proposed_release_date(self, data):
        release_date = data.get("proposed_release_date")
        first_run = data.get("is_first_run")

        if not self.instance or not release_date:
            return data

        if not first_run and release_date is not None:
            self.warnings["proposed_release_date"] = [
                NimbusExperiment.ERROR_FIRST_RUN_RELEASE_DATE
            ]
        return data

    def _validate_desktop_pref_rollouts(self, data):
        if self.instance.is_rollout:
            any_feature_sets_prefs = any(
                schema.sets_prefs
                for schemas_in_range in self.schemas_by_feature_id.values()
                for schema in schemas_in_range.schemas
            )

            if any_feature_sets_prefs and not data.get("prevent_pref_conflicts"):
                self.warnings["pref_rollout_reenroll"] = [
                    NimbusConstants.WARNING_ROLLOUT_PREF_REENROLL
                ]

        return data

    def validate(self, data):
        if self.instance.status == self.instance.Status.DRAFT:
            application = data.get("application")
            channel = data.get("channel")
            if application != NimbusExperiment.Application.DESKTOP and not channel:
                raise serializers.ValidationError(
                    {"channel": "Channel is required for this application."}
                )
            data = super().validate(data)
            data = self._validate_versions(data)
            data = self._validate_localizations(data)
            data = self._validate_feature_configs(data)
            data = self._validate_enrollment_targeting(data)
            data = self._validate_sticky_enrollment(data)
            data = self._validate_rollout_version_support(data)
            data = self._validate_bucket_duplicates(data)
            data = self._validate_proposed_release_date(data)
            if application == NimbusExperiment.Application.DESKTOP:
                data = self._validate_desktop_pref_rollouts(data)
            else:
                data = self._validate_languages_versions(data)
                data = self._validate_countries_versions(data)
        return data


class NimbusExperimentCloneSerializer(
    ExperimentNameValidatorMixin[NimbusExperiment], serializers.ModelSerializer
):
    parent_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=NimbusExperiment.objects.all()
    )
    name = serializers.CharField(min_length=1, max_length=80, required=True)
    rollout_branch_slug = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = NimbusExperiment
        fields = (
            "parent_slug",
            "name",
            "rollout_branch_slug",
        )

    def validate(self, data):
        data = super().validate(data)
        if rollout_branch_slug := data.get("rollout_branch_slug", None):
            parent = data.get("parent_slug")
            if not parent.branches.filter(slug=rollout_branch_slug).exists():
                raise serializers.ValidationError(
                    {
                        "rollout_branch_slug": (
                            f"Rollout branch {rollout_branch_slug} does not exist."
                        )
                    }
                )
        return data

    def save(self):
        parent = self.validated_data["parent_slug"]
        return parent.clone(
            self.validated_data["name"],
            self.context["user"],
            self.validated_data.get("rollout_branch_slug", None),
        )


class LocalizationError(Exception):
    """An error that occurs during localization substitution."""
