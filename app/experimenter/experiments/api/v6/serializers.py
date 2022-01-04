import json

from django.conf import settings
from packaging import version
from rest_framework import serializers

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusExperiment,
)


class NimbusBucketRangeSerializer(serializers.ModelSerializer):
    randomizationUnit = serializers.ReadOnlyField(
        source="isolation_group.randomization_unit"
    )
    namespace = serializers.ReadOnlyField(source="isolation_group.namespace")
    total = serializers.ReadOnlyField(source="isolation_group.total")

    class Meta:
        model = NimbusBucketRange
        fields = (
            "randomizationUnit",
            "namespace",
            "start",
            "count",
            "total",
        )


class NimbusBranchSerializerSingleFeature(serializers.ModelSerializer):
    feature = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "feature")

    def get_feature(self, obj):
        feature_config = None
        feature_config_slug = None
        feature_value = {}
        feature_enabled = False

        if obj.experiment.feature_configs.exists():
            feature_config = obj.experiment.feature_configs.all().order_by("slug").first()
            feature_config_slug = feature_config.slug
            if obj.feature_values.filter(feature_config=feature_config).exists():
                branch_feature_value = obj.feature_values.get(
                    feature_config=feature_config
                )
                feature_enabled = branch_feature_value.enabled
                try:
                    feature_value = json.loads(branch_feature_value.value)
                except json.JSONDecodeError:
                    # feature_value may be invalid JSON while the experiment is
                    # still being drafted
                    pass

        return {
            "featureId": feature_config_slug,
            "enabled": feature_enabled,
            "value": feature_value,
        }


class NimbusBranchSerializerMultiFeature(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "features")

    def get_features(self, obj):
        features = []
        for fv in obj.feature_values.all():
            feature_value = {
                "featureId": fv.feature_config and fv.feature_config.slug or "",
                "enabled": fv.enabled,
                "value": {},
            }
            try:
                feature_value["value"] = json.loads(fv.value)
            except Exception:
                # The value may still be invalid at this time
                pass
            features.append(feature_value)
        return features


class NimbusBranchSerializerMultiFeatureDesktop(NimbusBranchSerializerMultiFeature):
    feature = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "feature", "features")

    def get_feature(self, obj):
        return {
            "featureId": "this-is-included-for-desktop-pre-95-support",
            "enabled": False,
            "value": {},
        }


class NimbusExperimentSerializer(serializers.ModelSerializer):
    schemaVersion = serializers.ReadOnlyField(default=settings.NIMBUS_SCHEMA_VERSION)
    id = serializers.ReadOnlyField(source="slug")
    arguments = serializers.ReadOnlyField(default={})
    application = serializers.SerializerMethodField()
    appName = serializers.SerializerMethodField()
    appId = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    isEnrollmentPaused = serializers.ReadOnlyField(source="is_paused")
    bucketConfig = NimbusBucketRangeSerializer(source="bucket_range")
    featureIds = serializers.SerializerMethodField()
    probeSets = serializers.ReadOnlyField(default=[])
    outcomes = serializers.SerializerMethodField()
    startDate = serializers.DateField(source="start_date")
    endDate = serializers.DateField(source="end_date")
    proposedDuration = serializers.ReadOnlyField(source="proposed_duration")
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    referenceBranch = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = (
            "schemaVersion",
            "slug",
            "id",
            "arguments",
            "application",
            "appName",
            "appId",
            "channel",
            "userFacingName",
            "userFacingDescription",
            "isEnrollmentPaused",
            "bucketConfig",
            "featureIds",
            "probeSets",
            "outcomes",
            "branches",
            "targeting",
            "startDate",
            "endDate",
            "proposedDuration",
            "proposedEnrollment",
            "referenceBranch",
        )

    def get_application(self, obj):
        return self.get_appId(obj)

    def get_appName(self, obj):
        return obj.application_config.app_name

    def get_appId(self, obj):
        return obj.application_config.channel_app_id.get(obj.channel, "")

    def get_branches(self, obj):
        if obj.application == NimbusExperiment.Application.DESKTOP and version.parse(
            obj.firefox_min_version
        ) >= version.parse(NimbusExperiment.Version.FIREFOX_95):
            return NimbusBranchSerializerMultiFeatureDesktop(
                obj.branches.all(), many=True
            ).data

        return NimbusBranchSerializerSingleFeature(obj.branches.all(), many=True).data

    def get_featureIds(self, obj):
        return list(obj.feature_configs.all().values_list("slug", flat=True))

    def get_outcomes(self, obj):
        prioritized_outcomes = (
            ("primary", obj.primary_outcomes),
            ("secondary", obj.secondary_outcomes),
        )
        return [
            {"slug": slug, "priority": priority}
            for (priority, outcomes) in prioritized_outcomes
            for slug in outcomes
        ]

    def get_referenceBranch(self, obj):
        if obj.reference_branch:
            return obj.reference_branch.slug
