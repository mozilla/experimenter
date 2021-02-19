import json

import jsonschema
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.models.nimbus import (
    NimbusBranch,
    NimbusDocumentationLink,
    NimbusFeatureConfig,
    NimbusProbeSet,
)
from experimenter.kinto.tasks import nimbus_synchronize_preview_experiments_in_kinto


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


class NimbusExperimentProbeSetMixin:
    def validate_primary_probe_set_slugs(self, value):
        if len(value) > NimbusExperiment.MAX_PRIMARY_PROBE_SETS:
            raise serializers.ValidationError(
                "Exceeded maximum primary probe set limit of "
                f"{NimbusExperiment.MAX_PRIMARY_PROBE_SETS}."
            )
        return value

    def validate(self, data):
        """Validate the probe sets don't overlap and have no more than the max
        number of primary probesets.

        Note that the default DRF validation ensures all the probe id's are valid and
        it will not save overlapping probesets. It does not however throw an error with
        overlapping probesets, so that is checked explicitly here.

        """
        data = super().validate(data)
        primary_probe_set_slugs = set(data.get("primary_probe_set_slugs", []))
        secondary_probe_set_slugs = set(data.get("secondary_probe_set_slugs", []))
        if primary_probe_set_slugs.intersection(secondary_probe_set_slugs):
            raise serializers.ValidationError(
                {
                    "primary_probe_set_slugs": (
                        "Primary probe sets cannot overlap with secondary probe sets."
                    )
                }
            )
        return data

    def update(self, experiment, data):
        with transaction.atomic():
            if set(data.keys()).intersection(
                {"primary_probe_set_slugs", "secondary_probe_set_slugs"}
            ):
                experiment.probe_sets.clear()

            primary_probe_set_slugs = data.pop("primary_probe_set_slugs", [])
            secondary_probe_set_slugs = data.pop("secondary_probe_set_slugs", [])
            experiment = super().update(experiment, data)

            if primary_probe_set_slugs:
                for probe_set in primary_probe_set_slugs:
                    experiment.probe_sets.add(
                        probe_set, through_defaults={"is_primary": True}
                    )

            if secondary_probe_set_slugs:
                for probe_set in secondary_probe_set_slugs:
                    experiment.probe_sets.add(
                        probe_set, through_defaults={"is_primary": False}
                    )

        return experiment


class NimbusStatusRestrictionMixin:
    ALLOWS_STATUS_CHANGE_ONLY = (NimbusExperiment.Status.PREVIEW,)
    ALLOWS_UPDATE = (NimbusExperiment.Status.DRAFT,)
    VALID_STATUS_TRANSITIONS = {
        NimbusExperiment.Status.DRAFT: (
            NimbusExperiment.Status.PREVIEW,
            NimbusExperiment.Status.REVIEW,
        ),
        NimbusExperiment.Status.PREVIEW: (
            NimbusExperiment.Status.DRAFT,
            NimbusExperiment.Status.REVIEW,
        ),
    }

    def validate(self, data):
        data = super().validate(data)
        if self.instance:
            status = self.instance.status
            if status in self.ALLOWS_STATUS_CHANGE_ONLY:
                if set(data.keys()) != {"status"}:
                    raise serializers.ValidationError(
                        {
                            "experiment": [
                                f"Nimbus Experiment has status '{status}', only "
                                "status can be changed."
                            ]
                        }
                    )
            elif status not in self.ALLOWS_UPDATE:
                required_statuses = ", ".join(self.ALLOWS_UPDATE)
                raise serializers.ValidationError(
                    {
                        "experiment": [
                            f"Nimbus Experiment has status '{status}', but can only "
                            f"be changed when set to '{required_statuses}'."
                        ]
                    }
                )

        return data

    def validate_status(self, value):
        if (
            self.instance
            and value != self.instance.status
            and value not in self.VALID_STATUS_TRANSITIONS.get(self.instance.status, ())
        ):
            status = self.instance.status
            raise serializers.ValidationError(
                f"Nimbus Experiment status cannot transition from {status} to {value}."
            )

        return value


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


class NimbusExperimentSerializer(
    NimbusExperimentBranchMixin,
    NimbusExperimentDocumentationLinkMixin,
    NimbusExperimentProbeSetMixin,
    NimbusStatusRestrictionMixin,
    serializers.ModelSerializer,
):
    name = serializers.CharField(
        min_length=0, max_length=255, required=False, allow_blank=True
    )
    slug = serializers.ReadOnlyField()
    application = serializers.ChoiceField(
        choices=NimbusExperiment.Application.choices, required=False
    )
    public_description = serializers.CharField(
        min_length=0, max_length=1024, required=False, allow_blank=True
    )
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

    primary_probe_set_slugs = serializers.SlugRelatedField(
        many=True,
        queryset=NimbusProbeSet.objects.all(),
        required=False,
        slug_field="slug",
    )

    secondary_probe_set_slugs = serializers.SlugRelatedField(
        many=True,
        queryset=NimbusProbeSet.objects.all(),
        required=False,
        slug_field="slug",
    )
    population_percent = serializers.DecimalField(
        7, 4, min_value=0.0, max_value=100.0, required=False
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "status",
            "name",
            "slug",
            "risk_mitigation_link",
            "documentation_links",
            "hypothesis",
            "application",
            "public_description",
            "feature_config",
            "reference_branch",
            "treatment_branches",
            "primary_probe_set_slugs",
            "secondary_probe_set_slugs",
            "channel",
            "firefox_min_version",
            "population_percent",
            "proposed_duration",
            "proposed_enrollment",
            "targeting_config_slug",
            "total_enrolled_clients",
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
        super().__init__(instance=instance, data=data, **kwargs)

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

    def create(self, validated_data):
        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
                "owner": self.context["user"],
            }
        )
        return super().create(validated_data)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            experiment = super().save(*args, **kwargs)

            if experiment.should_allocate_bucket_range:
                experiment.allocate_bucket_range()

            if self.should_call_preview_task:
                nimbus_synchronize_preview_experiments_in_kinto.apply_async(countdown=5)

            generate_nimbus_changelog(experiment, self.context["user"])

            return experiment


class NimbusReadyForReviewSerializer(
    NimbusStatusRestrictionMixin, serializers.ModelSerializer
):
    public_description = serializers.CharField(required=True)
    proposed_duration = serializers.IntegerField(required=True)
    proposed_enrollment = serializers.IntegerField(required=True)
    population_percent = serializers.DecimalField(
        7, 4, min_value=0.0001, max_value=100.0, required=True
    )
    firefox_min_version = serializers.ChoiceField(
        NimbusExperiment.Version.choices, required=True
    )
    application = serializers.ChoiceField(
        NimbusExperiment.Application.choices, required=True
    )
    hypothesis = serializers.CharField(required=True)
    risk_mitigation_link = serializers.URLField(
        min_length=0, max_length=255, required=True
    )
    documentation_links = NimbusDocumentationLinkSerializer(many=True)
    targeting_config_slug = serializers.ChoiceField(
        NimbusExperiment.TargetingConfig.choices, required=True
    )
    reference_branch = NimbusBranchSerializer(required=True)
    treatment_branches = NimbusBranchSerializer(many=True)
    feature_config = serializers.PrimaryKeyRelatedField(
        queryset=NimbusFeatureConfig.objects.all(),
        allow_null=True,
    )

    class Meta:
        model = NimbusExperiment
        exclude = ("id",)

    def validate_reference_branch(self, value):
        if value["description"] == "":
            raise serializers.ValidationError("Description cannot be blank.")
        return value

    def validate_treatment_branches(self, value):
        errors = []
        for branch in value:
            error = None
            if branch["description"] == "":
                error = ["Description cannot be blank."]
            errors.append(error)

        if any(x is not None for x in errors):
            raise serializers.ValidationError(errors)
        return value

    def validate_hypothesis(self, value):
        if value == NimbusExperiment.HYPOTHESIS_DEFAULT.strip():
            raise serializers.ValidationError("Hypothesis cannot be the default value.")
        return value
