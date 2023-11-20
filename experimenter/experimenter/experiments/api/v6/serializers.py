import contextlib
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
    features = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "features")

    def get_features(self, obj):
        features = []
        for fv in obj.feature_values.all():
            feature_value = {
                "featureId": fv.feature_config and fv.feature_config.slug or "",
                "enabled": True,  # TODO: Remove after Desktop 104 is no longer supported
                "value": {},
            }

            with contextlib.suppress(Exception):
                # The value may still be invalid at this time
                feature_value["value"] = json.loads(fv.value)

            features.append(feature_value)
        return features


class NimbusBranchSerializerDesktop(NimbusBranchSerializer):
    feature = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "feature", "features")

    def get_feature(self, obj):
        return {
            "featureId": "this-is-included-for-desktop-pre-95-support",
            "enabled": False,  # TODO: Remove after Desktop 104 is no longer supported
            "value": {},
        }


class NimbusBranchSerializerMobile(NimbusBranchSerializer):
    feature = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "feature", "features")

    def get_feature(self, obj):
        return {
            "featureId": "this-is-included-for-mobile-pre-96-support",
            "enabled": False,  # TODO: Remove after Desktop 104 is no longer supported
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
    isRollout = serializers.ReadOnlyField(source="is_rollout")
    bucketConfig = NimbusBucketRangeSerializer(source="bucket_range")
    featureIds = serializers.SerializerMethodField()
    probeSets = serializers.ReadOnlyField(default=[])
    outcomes = serializers.SerializerMethodField()
    startDate = serializers.DateField(source="start_date")
    enrollmentEndDate = serializers.DateField(source="actual_enrollment_end_date")
    endDate = serializers.DateField(source="end_date")
    proposedDuration = serializers.ReadOnlyField(source="proposed_duration")
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    referenceBranch = serializers.SerializerMethodField()
    featureValidationOptOut = serializers.ReadOnlyField(
        source="is_client_schema_disabled"
    )
    localizations = serializers.SerializerMethodField()
    locales = serializers.SerializerMethodField()
    publishedDate = serializers.DateTimeField(source="published_date")

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
            "isRollout",
            "bucketConfig",
            "featureIds",
            "probeSets",
            "outcomes",
            "branches",
            "targeting",
            "startDate",
            "enrollmentEndDate",
            "endDate",
            "proposedDuration",
            "proposedEnrollment",
            "referenceBranch",
            "featureValidationOptOut",
            "localizations",
            "locales",
            "publishedDate",
        )

    def get_application(self, obj):
        return self.get_appId(obj)

    def get_appName(self, obj):
        return obj.application_config.app_name

    def get_appId(self, obj):
        return obj.application_config.channel_app_id.get(obj.channel, "")

    def get_branches(self, obj):
        serializer_cls = NimbusBranchSerializer
        if obj.application == NimbusExperiment.Application.DESKTOP:
            serializer_cls = NimbusBranchSerializerDesktop
        elif NimbusExperiment.Application.is_mobile(obj.application):
            serializer_cls = NimbusBranchSerializerMobile

        return serializer_cls(obj.branches.all(), many=True).data

    def get_featureIds(self, obj):
        return sorted(
            [feature_config.slug for feature_config in obj.feature_configs.all()]
        )

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

    def get_localizations(self, obj):
        if obj.is_localized:
            with contextlib.suppress(json.JSONDecodeError):
                return json.loads(obj.localizations)

    def get_locales(self, obj):
        locale_codes = [locale.code for locale in obj.locales.all()]
        if len(locale_codes):
            return locale_codes
