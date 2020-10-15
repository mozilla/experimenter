import json

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
            "featureId": obj.experiment.feature_config.slug,
            "enabled": obj.feature_enabled,
            "value": obj.feature_value,
        }


class NimbusExperimentSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="slug")
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    isEnrollmentPaused = serializers.ReadOnlyField(source="is_paused")
    bucketConfig = NimbusBucketRangeSerializer(source="bucket_range")
    probeSets = serializers.SerializerMethodField()
    branches = NimbusBranchSerializer(many=True)
    targeting = serializers.SerializerMethodField()
    startDate = serializers.ReadOnlyField(default=None)
    endDate = serializers.ReadOnlyField(default=None)
    proposedDuration = serializers.ReadOnlyField(source="proposed_duration")
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    referenceBranch = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = (
            "slug",
            "id",
            "application",
            "userFacingName",
            "userFacingDescription",
            "isEnrollmentPaused",
            "bucketConfig",
            "probeSets",
            "branches",
            "targeting",
            "startDate",
            "endDate",
            "proposedDuration",
            "proposedEnrollment",
            "referenceBranch",
        )

    def get_probeSets(self, obj):
        return list(obj.probe_sets.all().order_by("slug").values_list("slug", flat=True))

    def get_referenceBranch(self, obj):
        if obj.control_branch:
            return obj.control_branch.slug

    def get_targeting(self, obj):
        if obj.targeting_config:
            version_expr = ""
            if obj.firefox_min_version:
                version_expr = "{version_check} && ".format(
                    version_check=NimbusExperiment.TARGETING_VERSION.format(
                        version=obj.firefox_min_version
                    )
                )

            channels_expr = ""
            if obj.channels:
                channels_expr = "{channels_check} && ".format(
                    channels_check=NimbusExperiment.TARGETING_CHANNELS.format(
                        channels=json.dumps(obj.channels)
                    )
                )

            return f"{channels_expr}{version_expr}{obj.targeting_config.targeting}"
