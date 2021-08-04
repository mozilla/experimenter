import json

from django.conf import settings
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


class NimbusBranchSerializer(serializers.ModelSerializer):
    feature = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "feature")

    def get_feature(self, obj):
        return {
            "featureId": obj.experiment.feature_config.slug
            if obj.experiment.feature_config
            else None,
            "enabled": obj.feature_enabled,
            "value": json.loads(obj.feature_value) if obj.feature_value else {},
        }


class NimbusExperimentSerializer(serializers.ModelSerializer):
    schemaVersion = serializers.ReadOnlyField(default=settings.NIMBUS_SCHEMA_VERSION)
    id = serializers.ReadOnlyField(source="slug")
    arguments = serializers.ReadOnlyField(default={})
    application = serializers.SerializerMethodField()
    appName = serializers.SerializerMethodField()
    appId = serializers.SerializerMethodField()
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    isEnrollmentPaused = serializers.ReadOnlyField(source="is_paused")
    bucketConfig = NimbusBucketRangeSerializer(source="bucket_range")
    probeSets = serializers.ReadOnlyField(default=[])
    outcomes = serializers.SerializerMethodField()
    branches = NimbusBranchSerializer(many=True)
    startDate = serializers.DateField(source="start_date")
    endDate = serializers.DateField(source="end_date")
    proposedDuration = serializers.ReadOnlyField(source="proposed_duration")
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    referenceBranch = serializers.SerializerMethodField()
    featureIds = serializers.SerializerMethodField()

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
            "probeSets",
            "outcomes",
            "branches",
            "targeting",
            "startDate",
            "endDate",
            "proposedDuration",
            "proposedEnrollment",
            "referenceBranch",
            "featureIds",
        )

    def get_application(self, obj):
        return self.get_appId(obj)

    def get_appName(self, obj):
        return obj.application_config.app_name

    def get_appId(self, obj):
        return obj.application_config.channel_app_id.get(obj.channel, "")

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

    def get_featureIds(self, obj):
        feature_ids = []
        if obj.feature_config:
            feature_ids.append(obj.feature_config.slug)
        return feature_ids
