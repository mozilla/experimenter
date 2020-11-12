import json

from django.conf import settings
from rest_framework import serializers

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusExperiment,
    NimbusProbe,
    NimbusProbeSet,
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

    def to_representation(self, branch):
        data = super().to_representation(branch)
        if not branch.experiment.feature_config:
            data = {k: v for k, v in data.items() if k != "feature"}
        return data

    def get_feature(self, obj):
        if obj.experiment.feature_config:
            return {
                "featureId": obj.experiment.feature_config.slug,
                "enabled": obj.feature_enabled,
                "value": json.loads(obj.feature_value),
            }


class NimbusExperimentArgumentsSerializer(serializers.ModelSerializer):
    schemaVersion = serializers.ReadOnlyField(default=settings.NIMBUS_SCHEMA_VERSION)
    id = serializers.ReadOnlyField(source="slug")
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    isEnrollmentPaused = serializers.ReadOnlyField(source="is_paused")
    bucketConfig = NimbusBucketRangeSerializer(source="bucket_range")
    probeSets = serializers.SerializerMethodField()
    branches = NimbusBranchSerializer(many=True)
    targeting = serializers.SerializerMethodField()
    startDate = serializers.DateTimeField(source="start_date")
    endDate = serializers.DateTimeField(source="end_date")
    proposedDuration = serializers.ReadOnlyField(source="proposed_duration")
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    referenceBranch = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = (
            "schemaVersion",
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
        if obj.reference_branch:
            return obj.reference_branch.slug

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

            targeting_config = obj.targeting_config.targeting.format(experiment=obj)

            # TODO: Remove opt-out after Firefox 84 is the earliest supported Desktop
            return (
                f"{channels_expr}{version_expr}{targeting_config} "
                "&& 'app.shield.optoutstudies.enabled'|preferenceValue"
            )


class NimbusExperimentSerializer(NimbusExperimentArgumentsSerializer):
    arguments = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = NimbusExperimentArgumentsSerializer.Meta.fields + ("arguments",)

    def get_arguments(self, obj):
        return NimbusExperimentArgumentsSerializer(instance=obj).data


class NimbusProbeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusProbe
        fields = (
            "kind",
            "name",
            "event_category",
            "event_method",
            "event_object",
            "event_value",
        )


class NimbusProbeSetSerializer(serializers.ModelSerializer):
    probes = NimbusProbeSerializer(many=True)

    class Meta:
        model = NimbusProbeSet
        fields = ("name", "slug", "probes")
