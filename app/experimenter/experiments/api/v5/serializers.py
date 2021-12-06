import json
from collections import defaultdict

import jsonschema
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from experimenter.base.models import Country, Locale
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.models.nimbus import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusBranchScreenshot,
    NimbusDocumentationLink,
    NimbusFeatureConfig,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.outcomes import Outcomes


class ExperimentNameValidatorMixin:
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


class NimbusBranchSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    screenshots = NimbusBranchScreenshotSerializer(many=True, required=False)
    feature_enabled = serializers.BooleanField(required=False, write_only=True)
    feature_value = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )

    class Meta:
        model = NimbusBranch
        fields = (
            "id",
            "name",
            "description",
            "ratio",
            "screenshots",
            "feature_enabled",
            "feature_value",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["feature_enabled"] = False
        data["feature_value"] = ""

        if instance.feature_values.exists():
            feature_value = instance.feature_values.get()
            data["feature_enabled"] = feature_value.enabled
            data["feature_value"] = feature_value.value

        return data

    def validate_name(self, value):
        slug_name = slugify(value)
        if not slug_name:
            raise serializers.ValidationError(
                "Name needs to contain alphanumeric characters."
            )
        return value

    def validate(self, data):
        data = super().validate(data)
        if data.get("feature_enabled") and not data.get("feature_value"):
            raise serializers.ValidationError(
                {"feature_value": "A value must be supplied for an enabled feature."}
            )
        if data.get("feature_value") and not data.get("feature_enabled"):
            raise serializers.ValidationError(
                {
                    "feature_value": (
                        "feature_enabled must be specificed to include a feature_value."
                    )
                }
            )
        return data

    def create(self, data):
        data["slug"] = slugify(data["name"])
        screenshots = data.pop("screenshots", None)
        branch = super().create(data)

        if screenshots is not None:
            for screenshot_data in screenshots:
                serializer = NimbusBranchScreenshotSerializer(
                    data=screenshot_data, partial=True
                )
                if serializer.is_valid(raise_exception=True):
                    serializer.save(branch=branch)

        return branch

    def update(self, branch, data):
        with transaction.atomic():
            screenshots = data.pop("screenshots", None)
            branch = super().update(branch, data)

            if screenshots is not None:
                updated_screenshots = dict(
                    (x["id"], x) for x in screenshots if x.get("id", None)
                )
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

        return branch

    def save(self, *args, **kwargs):
        feature_enabled = self.validated_data.pop("feature_enabled", False)
        feature_value = self.validated_data.pop("feature_value", "")
        branch = super().save(*args, **kwargs)

        feature_config = None
        if branch.experiment.feature_configs.exists():
            feature_config = branch.experiment.feature_configs.get()

        branch.feature_values.all().delete()
        NimbusBranchFeatureValue.objects.create(
            branch=branch,
            feature_config=feature_config,
            enabled=feature_enabled,
            value=feature_value,
        )

        return branch


class NimbusExperimentBranchMixin:
    def validate(self, data):
        data = super().validate(data)
        data = self._validate_duplicate_branch_names(data)
        return data

    def _validate_duplicate_branch_names(self, data):
        if "reference_branch" in data and "treatment_branches" in data:
            ref_branch_name = data["reference_branch"]["name"]
            treatment_branch_names = [
                branch["name"] for branch in data["treatment_branches"]
            ]
            all_names = [ref_branch_name, *treatment_branch_names]
            unique_names = set(all_names)

            if len(all_names) != len(unique_names):
                raise serializers.ValidationError(
                    {
                        "reference_branch": {
                            "name": NimbusConstants.ERROR_DUPLICATE_BRANCH_NAME
                        },
                        "treatment_branches": [
                            {"name": NimbusConstants.ERROR_DUPLICATE_BRANCH_NAME}
                            for i in data["treatment_branches"]
                        ],
                    }
                )
        return data

    def update(self, experiment, data):
        with transaction.atomic():
            reference_branch_data = data.pop("reference_branch", None)
            treatment_branches_data = data.pop("treatment_branches", None)

            experiment = super().update(experiment, data)

            if reference_branch_data is not None:
                branch_id = reference_branch_data.pop("id", None)
                instance = None
                if experiment.reference_branch:
                    if branch_id == experiment.reference_branch.id:
                        instance = experiment.reference_branch
                    else:
                        experiment.reference_branch.delete()

                serializer = NimbusBranchSerializer(
                    instance, data=reference_branch_data, partial=True
                )
                if serializer.is_valid(raise_exception=True):
                    experiment.reference_branch = serializer.save(experiment=experiment)
                    experiment.save()

            if treatment_branches_data is not None:
                updated_branches = dict(
                    (x["id"], x) for x in treatment_branches_data if x.get("id", None)
                )
                for branch in experiment.treatment_branches:
                    branch_id = branch.id
                    if branch_id not in updated_branches:
                        branch.delete()
                    else:
                        serializer = NimbusBranchSerializer(
                            branch, data=updated_branches[branch_id], partial=True
                        )
                        if serializer.is_valid(raise_exception=True):
                            serializer.save()

                new_branches = (
                    x for x in treatment_branches_data if not x.get("id", None)
                )
                for branch_data in new_branches:
                    serializer = NimbusBranchSerializer(data=branch_data, partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save(experiment=experiment)

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


class NimbusStatusValidationMixin:
    def validate(self, data):
        data = super().validate(data)

        restrictive_statuses = {
            "status": NimbusConstants.STATUS_ALLOWS_UPDATE,
            "publish_status": NimbusConstants.PUBLISH_STATUS_ALLOWS_UPDATE,
        }

        if self.instance:
            for status_field, restricted_statuses in restrictive_statuses.items():
                current_status = getattr(self.instance, status_field)
                is_locked = current_status not in restricted_statuses
                modifying_fields = set(data.keys()) - set(
                    NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS
                )
                is_modifying_locked_fields = set(data.keys()).issubset(modifying_fields)
                if is_locked and is_modifying_locked_fields:
                    raise serializers.ValidationError(
                        {
                            "experiment": [
                                f"Nimbus Experiment has {status_field} "
                                f"'{current_status}', only "
                                f"{NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS} "
                                f"can be changed, not: {modifying_fields}"
                            ]
                        }
                    )

        return data


class NimbusStatusTransitionValidator:
    requires_context = True

    def __init__(self, transitions):
        self.transitions = transitions

    def __call__(self, value, serializer_field):
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


class NimbusExperimentSerializer(
    NimbusExperimentBranchMixin,
    NimbusStatusValidationMixin,
    NimbusExperimentDocumentationLinkMixin,
    ExperimentNameValidatorMixin,
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
    risk_mitigation_link = serializers.URLField(
        min_length=0, max_length=255, required=False, allow_blank=True
    )
    documentation_links = NimbusDocumentationLinkSerializer(many=True, required=False)
    hypothesis = serializers.CharField(
        min_length=0, max_length=1024, required=False, allow_blank=True
    )
    reference_branch = NimbusBranchSerializer(required=False)
    treatment_branches = NimbusBranchSerializer(many=True, required=False)
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
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
                transitions=NimbusConstants.VALID_STATUS_TRANSITIONS,
            )
        ],
    )
    publish_status = serializers.ChoiceField(
        choices=NimbusExperiment.PublishStatus.choices,
        required=False,
        validators=[
            NimbusStatusTransitionValidator(
                transitions=NimbusConstants.VALID_PUBLISH_STATUS_TRANSITIONS
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
    conclusion_recommendation = serializers.ChoiceField(
        choices=NimbusExperiment.ConclusionRecommendation.choices,
        allow_null=True,
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
            "feature_config",
            "warn_feature_schema",
            "firefox_min_version",
            "hypothesis",
            "is_rollout",
            "is_archived",
            "is_enrollment_paused",
            "locales",
            "name",
            "population_percent",
            "primary_outcomes",
            "proposed_duration",
            "proposed_enrollment",
            "public_description",
            "publish_status",
            "reference_branch",
            "risk_brand",
            "risk_mitigation_link",
            "risk_partner_related",
            "risk_revenue",
            "secondary_outcomes",
            "slug",
            "status_next",
            "status",
            "takeaways_summary",
            "targeting_config_slug",
            "total_enrolled_clients",
            "treatment_branches",
        ]

    def __init__(self, instance=None, data=None, **kwargs):
        self.should_call_preview_task = instance and (
            (
                instance.status == NimbusExperiment.Status.DRAFT
                and data.get("status") == NimbusExperiment.Status.PREVIEW
            )
            or (
                instance.status == NimbusExperiment.Status.PREVIEW
                and data.get("status") == NimbusExperiment.Status.DRAFT
            )
        )
        self.should_call_push_task = (
            data.get("publish_status") == NimbusExperiment.PublishStatus.APPROVED
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
        if publish_status == NimbusExperiment.PublishStatus.APPROVED and (
            self.instance.publish_status != NimbusExperiment.PublishStatus.IDLE
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

        valid_outcomes = set(
            [o.slug for o in Outcomes.by_application(self.instance.application)]
        )

        if valid_outcomes.intersection(value_set) != value_set:
            invalid_outcomes = value_set - valid_outcomes
            raise serializers.ValidationError(
                f"Invalid choices for primary outcomes: {invalid_outcomes}"
            )

        return value

    def validate_secondary_outcomes(self, value):
        value_set = set(value)
        valid_outcomes = set(
            [o.slug for o in Outcomes.by_application(self.instance.application)]
        )

        if valid_outcomes.intersection(value_set) != value_set:
            invalid_outcomes = value_set - valid_outcomes
            raise serializers.ValidationError(
                f"Invalid choices for secondary outcomes: {invalid_outcomes}"
            )

        return value

    def validate_status_next(self, value):
        valid_status_next = NimbusExperiment.VALID_STATUS_NEXT_VALUES.get(
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
        self.changelog_message = validated_data.pop("changelog_message")
        return super().update(experiment, validated_data)

    def create(self, validated_data):
        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
                "owner": self.context["user"],
                "channel": list(
                    NimbusExperiment.APPLICATION_CONFIGS[
                        validated_data["application"]
                    ].channel_app_id.keys()
                )[0],
            }
        )
        self.changelog_message = validated_data.pop("changelog_message")
        return super().create(validated_data)

    def save(self):
        feature_config_provided = "feature_config" in self.validated_data
        feature_config = self.validated_data.pop("feature_config", None)

        with transaction.atomic():
            # feature_configs must be set before we call super to make sure
            # the feature_config is available when the branches save their
            # feature_values
            if self.instance:
                if feature_config_provided:
                    self.instance.feature_configs.clear()

                if feature_config:
                    self.instance.feature_configs.add(feature_config)

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


class NimbusBranchScreenshotReadyForReviewSerializer(NimbusBranchScreenshotSerializer):
    # Round-trip serialization & validation for review can use a string path
    image = serializers.CharField(required=True)
    description = serializers.CharField(required=True)


class NimbusBranchReadyForReviewSerializer(NimbusBranchSerializer):
    screenshots = NimbusBranchScreenshotReadyForReviewSerializer(
        many=True, required=False
    )

    def validate_feature_value(self, value):
        if value:
            try:
                json.loads(value)
            except Exception as e:
                raise serializers.ValidationError(f"Invalid JSON: {e.msg}")
        return value


class NimbusReadyForReviewSerializer(serializers.ModelSerializer):
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
    reference_branch = NimbusBranchReadyForReviewSerializer(required=True)
    treatment_branches = NimbusBranchReadyForReviewSerializer(many=True)
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        allow_null=False,
        error_messages={"null": NimbusConstants.ERROR_REQUIRED_FEATURE_CONFIG},
        write_only=True,
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

    class Meta:
        model = NimbusExperiment
        exclude = ("id", "feature_configs")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = defaultdict(list)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["feature_config"] = None
        if instance.feature_configs.exists():
            data["feature_config"] = instance.feature_configs.get().id
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

        if any(x for x in errors):
            raise serializers.ValidationError(errors)
        return value

    def validate_hypothesis(self, value):
        if value == NimbusExperiment.HYPOTHESIS_DEFAULT.strip():
            raise serializers.ValidationError("Hypothesis cannot be the default value.")
        return value

    def _validate_feature_value_against_schema(self, schema, value):
        json_value = json.loads(value)
        try:
            jsonschema.validate(json_value, schema)
        except jsonschema.ValidationError as exc:
            return [exc.message]

    def _validate_feature_configs(self, data):
        feature_config = data.get("feature_config", None)
        warn_feature_schema = data.get("warn_feature_schema", False)

        if not feature_config or not feature_config.schema or not self.instance:
            return data

        if self.instance.application != feature_config.application:
            raise serializers.ValidationError(
                {
                    "feature_config": [
                        f"Feature Config application {feature_config.application} does "
                        f"not match experiment application {self.instance.application}."
                    ]
                }
            )

        schema = json.loads(feature_config.schema)
        error_result = {}
        if data["reference_branch"].get("feature_enabled"):
            errors = self._validate_feature_value_against_schema(
                schema, data["reference_branch"]["feature_value"]
            )
            if errors:
                if warn_feature_schema:
                    self.warnings["reference_branch"] = {"feature_value": errors}
                else:
                    error_result["reference_branch"] = {"feature_value": errors}

        treatment_branches_errors = []
        treatment_branches_warnings = []
        for branch_data in data["treatment_branches"]:
            branch_error = None
            branch_warning = None
            if branch_data.get("feature_enabled", False):
                errors = self._validate_feature_value_against_schema(
                    schema, branch_data["feature_value"]
                )
                if errors:
                    if warn_feature_schema:
                        branch_warning = {"feature_value": errors}
                    else:
                        branch_error = {"feature_value": errors}
            treatment_branches_errors.append(branch_error)
            treatment_branches_warnings.append(branch_warning)

        if any(x is not None for x in treatment_branches_warnings):
            self.warnings["treatment_branches"] = treatment_branches_warnings

        if any(x is not None for x in treatment_branches_errors):
            error_result["treatment_branches"] = treatment_branches_errors

        if error_result:
            raise serializers.ValidationError(error_result)

        return data

    def validate(self, attrs):
        application = attrs.get("application")
        channel = attrs.get("channel")
        if application != NimbusExperiment.Application.DESKTOP and not channel:
            raise serializers.ValidationError(
                {"channel": "Channel is required for this application."}
            )
        data = super().validate(attrs)
        data = self._validate_feature_configs(data)
        return data


class NimbusExperimentCloneSerializer(
    ExperimentNameValidatorMixin, serializers.ModelSerializer
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
        rollout_branch_slug = data.get("rollout_branch_slug", None)
        if rollout_branch_slug:
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
