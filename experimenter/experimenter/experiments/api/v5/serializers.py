from __future__ import annotations

import dataclasses
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, NotRequired, Optional, Self, TypedDict
from urllib.parse import urlparse

import jsonschema
import packaging
from django.db import models, transaction
from django.utils.text import slugify
from mozilla_nimbus_schemas.experimenter_apis.experiments.experiments import (
    ExperimentLocalizations,
)
from rest_framework import serializers

from experimenter.experiments.constants import (
    NimbusConstants,
    TargetingMultipleKintoCollectionsError,
)
from experimenter.experiments.jexl_utils import JEXLParser
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusBranchScreenshot,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusFeatureVersion,
    NimbusVersionedSchema,
)
from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader

logger = logging.getLogger()


def is_valid_http_url(s: Any):
    if not isinstance(s, str):
        return False

    try:
        url = urlparse(s)
    except Exception:  # pragma: no cover
        return False

    return url.scheme in ("http", "https")


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
            for item in iterable.order_by("feature_config__slug")
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


class NimbusDocumentationLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusDocumentationLink
        fields = (
            "title",
            "link",
        )


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
            "_start_date",
            "enrollment_duration",
            "_end_date",
            "results_url",
            "experiment_summary",
            "rollout",
            "hypothesis",
            "takeaways_metric_gain",
            "takeaways_gain_amount",
            "takeaways_qbr_learning",
            "takeaways_summary",
        ]

    def get_feature_configs(self, obj):
        sorted_features = sorted(
            obj.feature_configs.all(), key=lambda feature: feature.name
        )
        return ",".join([feature.name for feature in sorted_features])

    def get_results_url(self, obj):
        return f"{obj.experiment_url}results" if obj.results_ready else ""


class NimbusExperimentYamlSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(read_only=True, slug_field="email")
    hypothesis = serializers.SerializerMethodField()
    qa_status = serializers.SerializerMethodField()
    feature_configs = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()
    documentation_links = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    locales = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    targeting = serializers.SerializerMethodField()
    channels = serializers.SerializerMethodField()
    conclusion_recommendation_labels = serializers.SerializerMethodField()
    experiment_url = serializers.CharField(read_only=True)
    risk_flags = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    required_experiments = serializers.SerializerMethodField()
    excluded_experiments = serializers.SerializerMethodField()
    application_display = serializers.SerializerMethodField()
    parent_experiment = serializers.SerializerMethodField()
    results_data = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = [
            "name",
            "slug",
            "status",
            "public_description",
            "hypothesis",
            "is_rollout",
            "owner",
            "application_display",
            "channels",
            "feature_configs",
            "branches",
            "targeting",
            "firefox_min_version",
            "firefox_max_version",
            "population_percent",
            "is_sticky",
            "is_first_run",
            "locales",
            "countries",
            "languages",
            "projects",
            "proposed_duration",
            "proposed_enrollment",
            "total_enrolled_clients",
            "_start_date",
            "_enrollment_end_date",
            "_end_date",
            "published_date",
            "primary_outcomes",
            "secondary_outcomes",
            "segments",
            "risk_flags",
            "documentation_links",
            "qa_status",
            "qa_comment",
            "is_firefox_labs_opt_in",
            "firefox_labs_title",
            "firefox_labs_description",
            "conclusion_recommendation_labels",
            "takeaways_summary",
            "takeaways_metric_gain",
            "takeaways_gain_amount",
            "takeaways_qbr_learning",
            "project_impact",
            "next_steps",
            "experiment_url",
            "tags",
            "required_experiments",
            "excluded_experiments",
            "parent_experiment",
            "results_data",
        ]

    def get_hypothesis(self, obj):
        hypothesis = (obj.hypothesis or "").strip()
        if hypothesis and not hypothesis.startswith("If we <do this"):
            return hypothesis
        return None

    def get_qa_status(self, obj):
        if obj.qa_status and obj.qa_status != NimbusExperiment.QAStatus.NOT_SET:
            return obj.qa_status
        return None

    def get_feature_configs(self, obj):
        return [
            {"slug": fc.slug, "name": fc.name}
            for fc in sorted(obj.feature_configs.all(), key=lambda f: f.name)
        ]

    def get_branches(self, obj):
        ref_id = obj.reference_branch_id
        result = []
        for branch in sorted(obj.branches.all(), key=lambda b: b.slug):
            fv_slugs = sorted(
                fv.feature_config.slug
                for fv in branch.feature_values.all()
                if fv.feature_config
            )
            result.append(
                {
                    "name": branch.name,
                    "slug": branch.slug,
                    "description": branch.description,
                    "ratio": branch.ratio,
                    "is_control": branch.id == ref_id if ref_id else False,
                    "feature_config_slugs": fv_slugs,
                }
            )
        return result

    def get_documentation_links(self, obj):
        return [
            {"title": link.get_title_display(), "link": link.link}
            for link in obj.documentation_links.all()
        ]

    def get_projects(self, obj):
        return [p.name for p in obj.projects.all()]

    def get_locales(self, obj):
        locales = list(obj.locales.all())
        if not locales:
            return None
        return {
            "exclude": obj.exclude_locales,
            "codes": [loc.code for loc in locales],
        }

    def get_countries(self, obj):
        countries = list(obj.countries.all())
        if not countries:
            return None
        return {
            "exclude": obj.exclude_countries,
            "codes": [c.code for c in countries],
        }

    def get_languages(self, obj):
        languages = list(obj.languages.all())
        if not languages:
            return None
        return {
            "exclude": obj.exclude_languages,
            "codes": [lang.code for lang in languages],
        }

    def get_targeting(self, obj):
        tc = obj.targeting_config
        if tc:
            return {"name": tc.name, "description": tc.description}
        if obj.targeting_config_slug:
            return {"name": obj.targeting_config_slug, "description": ""}
        return None

    def get_channels(self, obj):
        result = []
        if obj.channels:
            result.extend(obj.channels)
        elif obj.channel:
            result.append(obj.channel)
        return [c for c in result if c]

    def get_tags(self, obj):
        return sorted(t.name for t in obj.tags.all())

    def get_required_experiments(self, obj):
        return sorted(f"{e.name} ({e.slug})" for e in obj.required_experiments.all())

    def get_excluded_experiments(self, obj):
        return sorted(f"{e.name} ({e.slug})" for e in obj.excluded_experiments.all())

    def get_conclusion_recommendation_labels(self, obj):
        if obj.conclusion_recommendations:
            return obj.conclusion_recommendation_labels
        return []

    def get_risk_flags(self, obj):
        flags = []
        if obj.risk_partner_related:
            flags.append("Partner Related")
        if obj.risk_revenue:
            flags.append("Revenue")
        if obj.risk_brand:
            flags.append("Brand")
        if obj.risk_message:
            flags.append("Message")
        if obj.risk_ai:
            flags.append("AI")
        return flags

    def get_application_display(self, obj):
        return obj.get_application_display()

    def get_parent_experiment(self, obj):
        if obj.parent:
            return f"{obj.parent.name} ({obj.parent.slug})"
        return None

    def get_results_data(self, obj):
        if not obj.results_data:
            return None

        v3 = obj.results_data.get("v3")
        if not v3:
            return None

        overall = v3.get("overall")
        if not overall:
            return None

        filtered_overall = {}
        for basis, segments in overall.items():
            filtered_segments = {}
            for segment, branches in segments.items():
                filtered_branches = {}
                for branch, branch_data_wrapper in branches.items():
                    bd = branch_data_wrapper.get("branch_data", {})
                    filtered_groups = {}
                    for group, metrics in bd.items():
                        filtered_metrics = {
                            metric: metric_data
                            for metric, metric_data in metrics.items()
                            if self._metric_is_significant(metric_data)
                        }
                        if filtered_metrics:
                            filtered_groups[group] = filtered_metrics

                    if filtered_groups:
                        filtered_branches[branch] = {
                            "branch_data": filtered_groups,
                            "is_control": branch_data_wrapper.get("is_control", False),
                        }

                if filtered_branches:
                    filtered_segments[segment] = filtered_branches

            if filtered_segments:
                filtered_overall[basis] = filtered_segments

        if not filtered_overall:
            return None

        result = {"v3": {"overall": filtered_overall}}
        if "other_metrics" in v3:
            result["v3"]["other_metrics"] = v3["other_metrics"]
        return result

    @staticmethod
    def _metric_is_significant(metric_data):
        significance = metric_data.get("significance", {})
        for branch_sig in significance.values():
            overall_sig = branch_sig.get("overall", {})
            for value in overall_sig.values():
                if value in ("positive", "negative"):
                    return True
        return False


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
    channels = serializers.MultipleChoiceField(
        choices=NimbusExperiment.Channel.choices,
        required=False,
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
    risk_message = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"null": NimbusConstants.ERROR_REQUIRED_QUESTION},
    )
    risk_ai = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"null": NimbusConstants.ERROR_REQUIRED_QUESTION},
    )
    segments = serializers.ListField(
        child=serializers.CharField(),
        required=False,
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

        self.desktop_setpref_schemas: Optional[
            dict[NimbusFeatureConfig, NimbusVersionedSchema]
        ] = None

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

    @dataclass
    class ValidateBranchesResult:
        class Fields(TypedDict):
            reference_branch: NotRequired[dict[str, Any]]
            treatment_branches: NotRequired[list[dict[str, Any]]]

        errors: Fields = dataclasses.field(default_factory=Fields)
        warnings: Fields = dataclasses.field(default_factory=Fields)

    def _validate_branches(
        self,
        *,
        data: dict[str, Any],
    ) -> ValidateBranchesResult:
        results = self.ValidateBranchesResult()

        if data.get("is_localized"):
            localizations = json.loads(data.get("localizations"))
        else:
            localizations = None

        kwargs = {
            "localizations": localizations,
            "channel": data.get("channel"),
            "suppress_errors": data.get("warn_feature_schema", False),
        }

        result = self._validate_branch(
            branch=data.get("reference_branch", {}),
            **kwargs,
        )
        if any(result.errors):
            results.errors["reference_branch"] = {"feature_values": result.errors}

        if any(result.warnings):
            results.warnings["reference_branch"] = {"feature_values": result.warnings}

        treatment_branches_errors = []
        treatment_branches_warnings = []

        for treatment_branch in data.get("treatment_branches", []):
            result = self._validate_branch(branch=treatment_branch, **kwargs)

            if any(result.errors):
                treatment_branches_errors.append({"feature_values": result.errors})
            else:
                treatment_branches_errors.append({})

            if any(result.warnings):
                treatment_branches_warnings.append({"feature_values": result.warnings})
            else:
                treatment_branches_warnings.append({})

        if any(treatment_branches_errors):
            results.errors["treatment_branches"] = treatment_branches_errors

        if any(treatment_branches_warnings):
            results.warnings["treatment_branches"] = treatment_branches_warnings

        return results

    @dataclass
    class ValidateBranchResult:
        class Fields(TypedDict):
            value: NotRequired[list[str]]

        errors: list[Fields] = dataclasses.field(default_factory=list)
        warnings: list[Fields] = dataclasses.field(default_factory=list)

        def append(self, result: NimbusReviewSerializer.ValidateFeatureResult):
            if result.errors:
                self.errors.append({"value": result.errors})
            else:
                self.errors.append({})

            if result.warnings:
                self.warnings.append({"value": result.warnings})
            else:
                self.warnings.append({})

    def _validate_branch(
        self,
        *,
        branch: dict[str, Any],
        channel: str,
        localizations: Optional[dict[str, Any]],
        suppress_errors: bool,
    ) -> ValidateBranchResult:
        results = self.ValidateBranchResult()

        feature_values = branch.get("feature_values", [])
        for feature_value_data in feature_values:
            feature_config: NimbusFeatureConfig = feature_value_data["feature_config"]

            feature_result = self._validate_feature_value(
                application=self.instance.application,
                channel=channel,
                feature_config=feature_config,
                feature_value=feature_value_data["value"],
                localizations=localizations,
                schemas_in_range=self.schemas_by_feature_id[feature_config.slug],
                suppress_errors=suppress_errors,
            )

            results.append(feature_result)

        return results

    @dataclass
    class ValidateFeatureResult:
        errors: list[str] = dataclasses.field(default_factory=list)
        warnings: list[str] = dataclasses.field(default_factory=list)

        def extend_with_result(self, result: Self):
            self.errors.extend(result.errors)
            self.warnings.extend(result.warnings)

        def extend(self, msgs: list[str], warning: bool):
            if warning:
                self.warnings.extend(msgs)
            else:
                self.errors.extend(msgs)

        def append(self, msg: str, warning: bool):
            if warning:
                self.warnings.append(msg)
            else:
                self.errors.append(msg)

    def _validate_feature_value(
        self,
        *,
        application: str,
        channel: str,
        feature_config: NimbusFeatureConfig,
        feature_value: str,
        schemas_in_range: NimbusFeatureConfig.VersionedSchemaRange,
        localizations: Optional[dict[str, Any]],
        suppress_errors: bool,
    ) -> ValidateFeatureResult:
        result = self.ValidateFeatureResult()

        if schemas_in_range.unsupported_in_range:
            result.append(
                NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_RANGE.format(
                    feature_config=feature_config.name,
                ),
                suppress_errors,
            )
            return result

        if schemas_in_range.unsupported_versions:
            unsupported_version_strs = [
                str(v) for v in schemas_in_range.unsupported_versions
            ]
            if len(unsupported_version_strs) == 1:
                unsupported_versions = unsupported_version_strs[0]
            else:
                min_unsupported_version = min(unsupported_version_strs)
                max_unsupported_version = max(unsupported_version_strs)
                unsupported_versions = (
                    f"{min_unsupported_version}-{max_unsupported_version}"
                )
            result.append(
                NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_VERSIONS.format(
                    feature_config=feature_config.name,
                    versions=unsupported_versions,
                ),
                suppress_errors,
            )

        if application == NimbusExperiment.Application.DESKTOP:
            result.extend_with_result(
                self._validate_feature_value_with_schema(
                    feature_config,
                    schemas_in_range,
                    feature_value,
                    localizations,
                    suppress_errors,
                ),
            )
        else:
            result.extend(
                self._validate_feature_value_with_fml(
                    schemas_in_range,
                    NimbusFmlLoader.create_loader(application, channel),
                    feature_config,
                    feature_value,
                ),
                suppress_errors,
            )

        return result

    def _validate_feature_value_with_schema(
        self,
        feature_config: NimbusFeatureConfig,
        schemas_in_range: NimbusFeatureConfig.VersionedSchemaRange,
        value: str,
        localizations: Optional[dict[str, Any]],
        suppress_errors: bool,
    ) -> ValidateFeatureResult:
        result = self.ValidateFeatureResult()

        json_value = json.loads(value)
        schema_versions = defaultdict(list)
        for schema in schemas_in_range.schemas:
            schema_versions[schema.schema].append(schema)

        for schema_str, schemas in schema_versions.items():
            if schema_str is None:
                continue
            json_schema = json.loads(schema_str)
            versions = [s.version for s in schemas]
            if not localizations:
                result.extend(
                    self._validate_schema(json_value, json_schema, versions),
                    suppress_errors,
                )
            else:
                for locale_code, substitutions in localizations.items():
                    try:
                        substituted_value = self._substitute_localizations(
                            json_value, substitutions, locale_code
                        )
                    except LocalizationError as e:
                        result.append(str(e), suppress_errors)
                        continue

                    if schema_errors := self._validate_schema(
                        substituted_value, json_schema, versions
                    ):
                        for schema_error, version in zip(schema_errors, versions):
                            err_msg = (
                                f"Schema validation errors occured during locale "
                                f"substitution for locale {locale_code}"
                            )

                            if version is not None:
                                err_msg += f" at version {version}"

                            result.append(err_msg, suppress_errors)
                            result.append(schema_error, suppress_errors)

        for schema in schemas_in_range.schemas:
            if not schema.is_early_startup:
                # Normally localized experiments cannot set prefs, but
                # isEarlyStartup features will always set prefs for all the
                # variables in the experiment
                if localizations:
                    continue

                # If the feature schema is not marked isEarlyStartup and it does
                # not have any setPref variables, then there is nothing to
                # check.
                if not schema.set_pref_vars:
                    continue

            result.extend_with_result(
                self._validate_desktop_feature_value_pref_lengths(
                    feature_config,
                    schema,
                    json_value,
                    suppress_errors,
                ),
            )

        if feature_config.slug == NimbusConstants.DESKTOP_PREFFLIPS_SLUG:
            result.extend_with_result(
                self._validate_desktop_pref_flips_value(
                    json_value,
                    schemas_in_range.min_version,
                    schemas_in_range.max_version,
                )
            )

        return result

    def _validate_desktop_pref_flips_value(
        self,
        value: dict[str, Any],
        min_version: packaging.version.Version,
        max_version: Optional[packaging.version.Version],
    ) -> ValidateFeatureResult:
        result = self.ValidateFeatureResult()

        if not self.desktop_setpref_schemas:
            schemas = (
                NimbusVersionedSchema.objects.filter(
                    NimbusFeatureVersion.objects.between_versions_q(
                        min_version,
                        max_version,
                        prefix="version",
                    ),
                    feature_config__application=NimbusExperiment.Application.DESKTOP,
                )
                .exclude(set_pref_vars={})
                .prefetch_related("feature_config", "version")
            )

            self.desktop_setpref_schemas = {}
            for schema in schemas:
                self.desktop_setpref_schemas.setdefault(schema.feature_config, []).append(
                    schema
                )

        for pref in value.get("prefs", {}):
            for feature_config, schemas in self.desktop_setpref_schemas.items():
                conflicting_versions = []

                for schema in schemas:
                    if pref in schema.set_pref_vars.values():
                        conflicting_versions.append(schema.version.as_packaging_version())

                if conflicting_versions:
                    if len(conflicting_versions) == 1:
                        versions = str(conflicting_versions[0])
                    else:
                        versions = (
                            f"{min(conflicting_versions)}-{max(conflicting_versions)}"
                        )

                    msg = NimbusConstants.WARNING_FEATURE_VALUE_IN_VERSIONS.format(
                        versions=versions,
                        warning=NimbusConstants.WARNING_PREF_FLIPS_PREF_CONTROLLED_BY_FEATURE.format(
                            pref=pref, feature_config_slug=feature_config.slug
                        ),
                    )

                    result.append(msg, warning=True)

        return result

    @classmethod
    def _validate_desktop_feature_value_pref_lengths(
        cls,
        feature_config: NimbusFeatureConfig,
        schema: NimbusVersionedSchema,
        feature_value: dict[str, Any],
        suppress_errors: bool,
    ) -> ValidateFeatureResult:
        result = cls.ValidateFeatureResult()

        for variable_name, variable_value in feature_value.items():
            if not schema.is_early_startup and variable_name not in schema.set_pref_vars:
                continue

            if isinstance(variable_value, (list, dict)):
                variable_value = json.dumps(variable_value)
            elif not isinstance(variable_value, str):
                # int and bool are not serialized to strings
                continue

            pref_len = len(variable_value)

            if pref_len > NimbusConstants.LARGE_PREF_ERROR_LEN:
                message_fmt = NimbusConstants.ERROR_LARGE_PREF
            elif pref_len > NimbusConstants.LARGE_PREF_WARNING_LEN:
                message_fmt = NimbusConstants.WARNING_LARGE_PREF
            else:
                continue

            if schema.is_early_startup:
                reason = NimbusConstants.IS_EARLY_STARTUP_REASON.format(
                    feature=feature_config.name
                )
            else:
                reason = NimbusConstants.SET_PREF_REASON

            message = message_fmt.format(
                variable=variable_name,
                reason=reason,
            )

            if schema.version:
                message += f" at version {schema.version}"

            # If the pref is over the error threshold, then this error cannot be
            # supressed as a warning.
            as_warning = (
                suppress_errors and pref_len <= NimbusConstants.LARGE_PREF_ERROR_LEN
            )

            result.append(message, as_warning)

        return result

    @classmethod
    def _validate_feature_value_with_fml(
        cls,
        schemas_in_range: NimbusFeatureConfig.VersionedSchemaRange,
        loader: NimbusFmlLoader,
        feature_config: NimbusFeatureConfig,
        blob: str,
    ) -> list[str]:
        errors = []
        schema_errors_versions = defaultdict(set)
        for schema in schemas_in_range.schemas:
            for fml_error in loader.get_fml_errors(
                blob, feature_config.slug, schema.version
            ):
                schema_errors_versions[fml_error.message].add(schema.version)

        for fml_error, versions in schema_errors_versions.items():
            version_strs = [str(v) for v in versions]
            min_version = min(version_strs)
            max_version = max(version_strs)
            errors.append(
                NimbusConstants.ERROR_FEATURE_VALUE_IN_VERSIONS.format(
                    error=fml_error, versions=f"{min_version}-{max_version}"
                )
            )

        return errors

    @classmethod
    def _validate_schema(
        cls,
        obj: Any,
        schema: dict[str, Any],
        versions: list[Optional[NimbusFeatureVersion]],
    ) -> list[str]:
        try:
            jsonschema.validate(obj, schema, resolver=NestedRefResolver(schema))
        except jsonschema.ValidationError as e:
            err_msg = e.message
            return [
                f"{err_msg} at version {version}" if version is not None else err_msg
                for version in versions
            ]

        return []

    def _validate_feature_configs(self, data):
        feature_configs = data.get("feature_configs", [])

        min_version = None
        max_version = None
        if not NimbusExperiment.Application.is_web(self.instance.application):
            raw_min_version = data.get("firefox_min_version", "")
            raw_max_version = data.get("firefox_max_version", "")

            # We've already validated the versions in _validate_versions.
            min_version = NimbusExperiment.Version.parse(raw_min_version)
            if raw_max_version:
                max_version = NimbusExperiment.Version.parse(raw_max_version)

        errors = {
            "feature_configs": [
                f"Feature Config application {feature_config.application} "
                f"does not match experiment application "
                f"{self.instance.application}."
            ]
            for feature_config in feature_configs
            if self.instance.application != feature_config.application
        }
        if errors:
            # This error can't be dismissed by the warn_feature_schema flag.
            raise serializers.ValidationError(errors)

        reference_branch = data.get("reference_branch", {})

        if errors := self._validate_target_kinto_collections(data, feature_configs):
            raise serializers.ValidationError(
                {
                    "feature_configs": errors,
                }
            )

        # Cache the versioned schema range for each feature so we can re-use
        # them in the validation for each branch.
        self.schemas_by_feature_id = {
            feature_config.slug: feature_config.get_versioned_schema_range(
                min_version,
                max_version,
            )
            for feature_config in (
                feature_value_data["feature_config"]
                for feature_value_data in reference_branch.get(
                    "feature_values",
                    [],
                )
            )
        }

        result = self._validate_branches(data=data)

        if any(result.warnings):
            self.warnings.update(result.warnings)

        if any(result.errors):
            raise serializers.ValidationError(result.errors)

        return data

    def _validate_target_kinto_collections(self, data, feature_configs):
        errors = []

        application_config = self.instance.application_config

        try:
            application_config.get_kinto_collection_for_feature_ids(
                [fc.slug for fc in feature_configs], data.get("firefox_min_version", "")
            )
        except TargetingMultipleKintoCollectionsError as e:
            errors.append(NimbusConstants.ERROR_INCOMPATIBLE_FEATURES)

            feature_collection_pairs = [
                (feature_id, collection)
                for collection, feature_ids in e.target_collections.items()
                for feature_id in feature_ids
            ]
            feature_collection_pairs.sort()

            for feature_id, collection in feature_collection_pairs:
                errors.append(
                    NimbusConstants.ERROR_FEATURE_TARGET_COLLECTION.format(
                        feature_id=feature_id,
                        collection=collection,
                    )
                )

        return errors

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
                        NimbusExperiment.ERROR_FIREFOX_VERSION_MIN_SUPPORTED
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
                        NimbusExperiment.ERROR_FIREFOX_VERSION_MIN_SUPPORTED
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

    def _validate_risk_ai_version(self, data):
        risk_ai = data.get("risk_ai")
        firefox_min_version = data.get("firefox_min_version")
        application = data.get("application")

        if (
            risk_ai
            and application == NimbusExperiment.Application.DESKTOP
            and firefox_min_version
            and NimbusExperiment.Version.parse(firefox_min_version)
            < NimbusExperiment.Version.parse(NimbusExperiment.AI_RISK_MIN_VERSION)
        ):
            raise serializers.ValidationError(
                {
                    "firefox_min_version": [
                        NimbusConstants.ERROR_FIREFOX_VERSION_MIN_148_FOR_AI_RISK
                    ],
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

    def _validate_targeting_parses(self, data):
        expression = self.instance.targeting

        try:
            JEXLParser().parse(expression)
        except Exception as e:
            raise serializers.ValidationError(
                NimbusConstants.ERROR_CANNOT_PARSE_TARGETING
            ) from e

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

        try:
            ExperimentLocalizations.model_validate(localizations)
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
                bool(schema.set_pref_vars)
                for schemas_in_range in self.schemas_by_feature_id.values()
                for schema in schemas_in_range.schemas
            )

            if any_feature_sets_prefs and not data.get("prevent_pref_conflicts"):
                self.warnings["pref_rollout_reenroll"] = [
                    NimbusConstants.WARNING_ROLLOUT_PREF_REENROLL
                ]

        return data

    def _validate_desktop_pref_flips(self, data):
        if not any(
            fc.slug == NimbusConstants.DESKTOP_PREFFLIPS_SLUG
            for fc in data.get("feature_configs", [])
        ):
            return data

        min_version = NimbusExperiment.Version.parse(data["firefox_min_version"])
        channels = data.get("channels", [])

        # We have already validated that the feature is supported by the current
        # version. However, we don't keep track of per-channel manifests. The
        # prefFlips feature landed in 128 Nightly as a placeholder and was only
        # implemented in 129 Nightly+, but it was uplifted to 128 ESR.
        esr_only = set(channels) == {NimbusExperiment.Channel.ESR}

        if esr_only:
            return data

        elif min_version.major == 128:
            raise serializers.ValidationError(
                {
                    "firefox_min_version": (
                        NimbusConstants.ERROR_DESKTOP_PREFFLIPS_128_ESR_ONLY
                    )
                }
            )

        return data

    def _validate_feature_value_variables(self, data):
        warn_feature_schema = data.get("warn_feature_schema", False)
        feature_configs = data.get("feature_configs", [])
        reference_branch = data.get("reference_branch", {})
        treatment_branches = data.get("treatment_branches", [])
        branches = [reference_branch, *treatment_branches]

        feature_branch_variables = {
            feature_config: {
                branch["id"]: set(json.loads(feature_value["value"]).keys())
                for branch in branches
                for feature_value in branch["feature_values"]
                if feature_value["feature_config"] == feature_config
            }
            for feature_config in feature_configs
        }

        errors = {
            "reference_branch": {"feature_values": [{} for _ in feature_configs]},
            "treatment_branches": [
                {"feature_values": [{} for _ in feature_configs]}
                for _ in treatment_branches
            ],
        }

        found_errors = False
        for feature_config_i, feature_config in enumerate(feature_configs):
            if any(
                schema.has_remote_schema
                for schema in self.schemas_by_feature_id[feature_config.slug].schemas
            ):
                continue

            branches_variables = feature_branch_variables[feature_config].values()
            all_variables = set().union(*branches_variables)

            for branch_i, branch in enumerate(branches):
                branch_variables = feature_branch_variables[feature_config][branch["id"]]
                if branch_variables != all_variables:
                    found_errors = True

                    error = (
                        NimbusConstants.ERROR_FEATURE_VALUE_DIFFERENT_VARIABLES.format(
                            variables=", ".join(all_variables - branch_variables)
                        )
                    )

                    if branch == reference_branch:
                        errors["reference_branch"]["feature_values"][feature_config_i] = {
                            "value": [error]
                        }
                    else:
                        errors["treatment_branches"][branch_i - 1]["feature_values"][
                            feature_config_i
                        ] = {"value": [error]}

        if found_errors:
            if warn_feature_schema:
                self.warnings.update(errors)
            else:
                raise serializers.ValidationError(errors)

        return data

    def _validate_primary_secondary_outcomes(self, data):
        primary_outcomes = set(data.get("primary_outcomes", []))
        secondary_outcomes = set(data.get("secondary_outcomes", []))

        if primary_outcomes.intersection(secondary_outcomes):
            raise serializers.ValidationError(
                {
                    "primary_outcomes": [
                        NimbusExperiment.ERROR_PRIMARY_SECONDARY_OUTCOMES_INTERSECTION
                    ],
                    "secondary_outcomes": [
                        NimbusExperiment.ERROR_PRIMARY_SECONDARY_OUTCOMES_INTERSECTION
                    ],
                }
            )

        return data

    def _validate_firefox_labs(self, data):
        if not data.get("is_firefox_labs_opt_in"):
            return data

        min_version = NimbusExperiment.Version.parse(data.get("firefox_min_version"))
        required_min_version = NimbusExperiment.FIREFOX_LABS_MIN_VERSION.get(
            self.instance.application
        )

        if required_min_version is None:
            raise serializers.ValidationError(
                {
                    "is_firefox_labs_opt_in": (
                        NimbusExperiment.ERROR_FIREFOX_LABS_UNSUPPORTED_APPLICATION
                    ),
                }
            )
        required_min_version = NimbusExperiment.Version.parse(required_min_version)
        if min_version < required_min_version:
            raise serializers.ValidationError(
                {
                    "firefox_min_version": (
                        NimbusExperiment.ERROR_FIREFOX_LABS_MIN_VERSION.format(
                            version=required_min_version
                        )
                    ),
                }
            )

        if not data.get("is_rollout"):
            raise serializers.ValidationError(
                {"is_rollout": NimbusExperiment.ERROR_FIREFOX_LABS_ROLLOUT_REQUIRED}
            )

        errors = {
            field: [NimbusExperiment.ERROR_FIREFOX_LABS_REQUIRED_FIELD]
            for field in (
                "firefox_labs_title",
                "firefox_labs_description",
                "firefox_labs_group",
            )
            if not len((data.get(field) or "").strip())
        }

        group = data.get("firefox_labs_group")
        if required_min_version := NimbusExperiment.FIREFOX_LABS_GROUP_AVAILABILITY[
            self.instance.application
        ].get(group):
            required_min_version = NimbusExperiment.Version.parse(required_min_version)
            if min_version < required_min_version:
                raise serializers.ValidationError(
                    {
                        "firefox_labs_group": (
                            NimbusExperiment.ERROR_FIREFOX_LABS_GROUP_MIN_VERSION.format(
                                version=required_min_version
                            )
                        ),
                    }
                )

        if description_links := (
            data.get("firefox_labs_description_links") or ""
        ).strip():
            try:
                description_links_obj = json.loads(description_links)
            except Exception:
                errors["firefox_labs_description_links"] = [
                    NimbusExperiment.ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_JSON,
                ]
            else:
                if isinstance(description_links_obj, dict):
                    if not all(
                        is_valid_http_url(value)
                        for value in description_links_obj.values()
                    ):
                        errors["firefox_labs_description_links"] = [
                            NimbusExperiment.ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_HTTP_URLS,
                        ]

                elif (
                    not isinstance(description_links_obj, dict)
                    and description_links_obj is not None
                ):
                    errors["firefox_labs_description_links"] = [
                        NimbusExperiment.ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_JSON,
                    ]

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def validate(self, data):
        application = data.get("application")
        channel = data.get("channel")
        if application != NimbusExperiment.Application.DESKTOP and not channel:
            raise serializers.ValidationError(
                {"channel": "Channel is required for this application."}
            )
        channels = data.get("channels")
        if application == NimbusExperiment.Application.DESKTOP and not channels:
            raise serializers.ValidationError(
                {"channels": "Please select at least one channel."}
            )
        data = super().validate(data)
        data = self._validate_versions(data)
        data = self._validate_risk_ai_version(data)
        data = self._validate_localizations(data)
        data = self._validate_feature_configs(data)
        data = self._validate_enrollment_targeting(data)
        data = self._validate_targeting_parses(data)
        data = self._validate_sticky_enrollment(data)
        data = self._validate_bucket_duplicates(data)
        data = self._validate_proposed_release_date(data)
        data = self._validate_feature_value_variables(data)
        data = self._validate_primary_secondary_outcomes(data)
        data = self._validate_firefox_labs(data)
        if application == NimbusExperiment.Application.DESKTOP:
            data = self._validate_desktop_pref_rollouts(data)
            data = self._validate_desktop_pref_flips(data)
        return data


class LocalizationError(Exception):
    """An error that occurs during localization substitution."""


class FmlErrorSerializer(serializers.Serializer):
    line = serializers.IntegerField()
    col = serializers.IntegerField()
    highlight = serializers.CharField()
    message = serializers.CharField()


class FmlFeatureValueSerializer(serializers.Serializer):
    featureSlug = serializers.CharField()
    featureValue = serializers.CharField()

    def update(self, instance, validated_data):
        fml_loader = NimbusFmlLoader.create_loader(instance.application, instance.channel)
        feature_slug = validated_data["featureSlug"]
        feature_value = validated_data["featureValue"]
        return fml_loader.get_fml_errors(feature_value, feature_slug)

    @property
    def data(self):
        return FmlErrorSerializer(self.instance, many=True).data
