import json

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
    NimbusDocumentationLink,
    NimbusFeatureConfig,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.outcomes import Outcomes


class NimbusBranchSerializer(serializers.ModelSerializer):
    def validate_name(self, value):
        slug_name = slugify(value)
        if not slug_name:
            raise serializers.ValidationError(
                "Name needs to contain alphanumeric characters."
            )
        return value

    def validate(self, data):
        data = super().validate(data)
        if data.get("feature_enabled", False) and "feature_value" not in data:
            raise serializers.ValidationError(
                {
                    "feature_enabled": (
                        "feature_value must be specified if feature_enabled is True."
                    )
                }
            )
        if data.get("feature_value") and "feature_enabled" not in data:
            raise serializers.ValidationError(
                {
                    "feature_value": (
                        "feature_enabled must be specificed to include a feature_value."
                    )
                }
            )
        return data

    class Meta:
        model = NimbusBranch
        fields = (
            "name",
            "description",
            "ratio",
            "feature_enabled",
            "feature_value",
        )


class NimbusExperimentBranchMixin:
    def _validate_feature_value_against_schema(self, schema, value):
        try:
            json_value = json.loads(value)
        except json.JSONDecodeError as exc:
            return [exc.msg]
        try:
            jsonschema.validate(json_value, schema)
        except jsonschema.ValidationError as exc:
            return [exc.message]

    def validate(self, data):
        data = super().validate(data)
        data = self._validate_duplicate_branch_names(data)
        data = self._validate_feature_configs(data)
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

    def _validate_feature_configs(self, data):
        # Determine if we require a feature_config
        feature_config_required = data.get("reference_branch", {}).get(
            "feature_enabled", False
        )
        for branch in data.get("treatment_branches", []):
            branch_required = branch.get("feature_enabled", False)
            feature_config_required = feature_config_required or branch_required
        feature_config = data.get("feature_config", None)
        if feature_config_required and not feature_config:
            raise serializers.ValidationError(
                {
                    "feature_config": [
                        "Feature Config required when a branch has feature enabled."
                    ]
                }
            )

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
                error_result["reference_branch"] = {"feature_value": errors}

        treatment_branches_errors = []
        for branch_data in data["treatment_branches"]:
            branch_error = None
            if branch_data.get("feature_enabled", False):
                errors = self._validate_feature_value_against_schema(
                    schema, branch_data["feature_value"]
                )
                if errors:
                    branch_error = {"feature_value": errors}
            treatment_branches_errors.append(branch_error)

        if any(x is not None for x in treatment_branches_errors):
            error_result["treatment_branches"] = treatment_branches_errors

        if error_result:
            raise serializers.ValidationError(error_result)

        return data

    def create(self, validated_data):
        experiment = super().create(validated_data)
        experiment.reference_branch = NimbusBranch.objects.create(
            experiment=experiment, name="Control", feature_enabled=False
        )
        experiment.save()
        return experiment

    def update(self, experiment, data):
        with transaction.atomic():
            if set(data.keys()).intersection({"reference_branch", "treatment_branches"}):
                experiment.delete_branches()

            control_branch_data = data.pop("reference_branch", {})
            treatment_branches_data = data.pop("treatment_branches", [])

            experiment = super().update(experiment, data)

            if control_branch_data:
                experiment.reference_branch = NimbusBranch.objects.create(
                    experiment=experiment,
                    slug=slugify(control_branch_data["name"]),
                    **control_branch_data,
                )
                experiment.save()

            if treatment_branches_data:
                for branch_data in treatment_branches_data:
                    NimbusBranch.objects.create(
                        experiment=experiment,
                        slug=slugify(branch_data["name"]),
                        **branch_data,
                    )

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
    serializers.ModelSerializer,
):
    name = serializers.CharField(
        min_length=0, max_length=255, required=False, allow_blank=True
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

    class Meta:
        model = NimbusExperiment
        fields = [
            "status",
            "status_next",
            "publish_status",
            "name",
            "slug",
            "risk_mitigation_link",
            "documentation_links",
            "hypothesis",
            "application",
            "public_description",
            "is_enrollment_paused",
            "feature_config",
            "reference_branch",
            "treatment_branches",
            "primary_outcomes",
            "secondary_outcomes",
            "channel",
            "firefox_min_version",
            "population_percent",
            "proposed_duration",
            "proposed_enrollment",
            "targeting_config_slug",
            "total_enrolled_clients",
            "changelog_message",
            "risk_partner_related",
            "risk_revenue",
            "risk_brand",
            "countries",
            "locales",
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

    def validate_publish_status(self, publish_status):
        if publish_status == NimbusExperiment.PublishStatus.APPROVED and (
            self.instance.publish_status != NimbusExperiment.PublishStatus.IDLE
            and not self.instance.can_review(self.context["user"])
        ):
            raise serializers.ValidationError(
                f'{self.context["user"]} can not review this experiment.'
            )
        return publish_status

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

    def save(self, *args, **kwargs):
        with transaction.atomic():
            experiment = super().save(*args, **kwargs)

            if experiment.has_filter(experiment.Filters.SHOULD_ALLOCATE_BUCKETS):
                experiment.allocate_bucket_range()

            if self.should_call_preview_task:
                nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)

            if self.should_call_push_task:
                collection = NimbusExperiment.KINTO_APPLICATION_COLLECTION[
                    experiment.application
                ]
                nimbus_check_kinto_push_queue_by_collection.apply_async(
                    countdown=5, args=[collection]
                )

            generate_nimbus_changelog(
                experiment, self.context["user"], message=self.changelog_message
            )

            return experiment


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
    reference_branch = NimbusBranchSerializer(required=True)
    treatment_branches = NimbusBranchSerializer(many=True)
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        allow_null=False,
        error_messages={"null": NimbusConstants.ERROR_REQUIRED_FEATURE_CONFIG},
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
        exclude = ("id",)

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

    def validate(self, attrs):
        application = attrs.get("application")
        channel = attrs.get("channel")
        if application != NimbusExperiment.Application.DESKTOP and not channel:
            raise serializers.ValidationError(
                {"channel": "Channel is required for this application."}
            )
        return super().validate(attrs)
