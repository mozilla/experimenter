import contextlib
import datetime
import json

from django.conf import settings
from rest_framework import serializers

from experimenter.experiments.jexl_to_sql import jexl_to_sql
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
                "featureId": (fv.feature_config and fv.feature_config.slug) or "",
                "value": {},
            }

            with contextlib.suppress(Exception):
                # The value may still be invalid at this time
                feature_value["value"] = json.loads(fv.value)

            features.append(feature_value)
        return features


class NimbusBranchSerializerDesktop(NimbusBranchSerializer):
    feature = serializers.SerializerMethodField()
    firefoxLabsTitle = serializers.ReadOnlyField(source="firefox_labs_title")

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "feature", "features", "firefoxLabsTitle")

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
    appName = serializers.SerializerMethodField()
    appId = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()
    channels = serializers.SerializerMethodField()
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    isEnrollmentPaused = serializers.ReadOnlyField(source="is_paused")
    isRollout = serializers.ReadOnlyField(source="is_rollout")
    isHoldback = serializers.ReadOnlyField(source="is_holdback")
    doRerun = serializers.ReadOnlyField(source="do_rerun")
    doRerunTimestamp = serializers.ReadOnlyField(source="do_rerun_timestamp")
    bucketConfig = NimbusBucketRangeSerializer(source="bucket_range")
    featureIds = serializers.SerializerMethodField()
    outcomes = serializers.SerializerMethodField()
    segments = serializers.SerializerMethodField()
    startDate = serializers.DateField(source="start_date")
    enrollmentEndDate = serializers.SerializerMethodField()
    endDate = serializers.SerializerMethodField()
    proposedDuration = serializers.ReadOnlyField(source="proposed_duration")
    proposedEnrollment = serializers.SerializerMethodField()
    referenceBranch = serializers.SerializerMethodField()
    featureValidationOptOut = serializers.ReadOnlyField(
        source="is_client_schema_disabled"
    )
    localizations = serializers.SerializerMethodField()
    locales = serializers.SerializerMethodField()
    publishedDate = serializers.DateTimeField(source="published_date")
    isFirefoxLabsOptIn = serializers.ReadOnlyField(source="is_firefox_labs_opt_in")
    firefoxLabsTitle = serializers.ReadOnlyField(source="firefox_labs_title")
    firefoxLabsDescription = serializers.ReadOnlyField(source="firefox_labs_description")
    firefoxLabsDescriptionLinks = serializers.SerializerMethodField()
    firefoxLabsGroup = serializers.ReadOnlyField(source="firefox_labs_group")
    requiresRestart = serializers.ReadOnlyField(source="requires_restart")
    targetingSql = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = (
            "schemaVersion",
            "slug",
            "id",
            "appName",
            "appId",
            "channel",
            "channels",
            "userFacingName",
            "userFacingDescription",
            "isEnrollmentPaused",
            "isRollout",
            "isHoldback",
            "doRerun",
            "doRerunTimestamp",
            "bucketConfig",
            "featureIds",
            "outcomes",
            "segments",
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
            "isFirefoxLabsOptIn",
            "firefoxLabsTitle",
            "firefoxLabsDescription",
            "firefoxLabsDescriptionLinks",
            "firefoxLabsGroup",
            "requiresRestart",
            "targetingSql",
        )

    def get_targetingSql(self, obj):
        if obj.status != NimbusExperiment.Status.DRAFT:
            return None
        result = jexl_to_sql(obj.targeting)
        if result.sql is None and not result.warnings:
            return None
        return {
            "sql": result.sql,
            "warnings": result.warnings,
        }

    def _holdback_enrollment_end(self, obj):
        if obj.is_holdback and not obj.end_date and not obj.actual_enrollment_end_date:
            return datetime.date.today() - datetime.timedelta(
                days=settings.HOLDBACK_OBSERVATION_DAYS
            )
        return None

    def get_enrollmentEndDate(self, obj):
        holdback_end = self._holdback_enrollment_end(obj)
        if holdback_end:
            return holdback_end.isoformat()
        enrollment_end = obj.actual_enrollment_end_date
        return enrollment_end.isoformat() if enrollment_end else None

    def get_endDate(self, obj):
        holdback_end = self._holdback_enrollment_end(obj)
        if holdback_end:
            return (
                holdback_end + datetime.timedelta(days=settings.HOLDBACK_OBSERVATION_DAYS)
            ).isoformat()
        return obj.end_date.isoformat() if obj.end_date else None

    def get_proposedEnrollment(self, obj):
        holdback_end = self._holdback_enrollment_end(obj)
        if holdback_end and obj.start_date:
            return (holdback_end - obj.start_date).days
        return obj.proposed_enrollment

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

    def get_channels(self, obj):
        if obj.channels:
            return obj.channels
        elif obj.channel:
            return [obj.channel]
        return []

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

    def get_segments(self, obj):
        return [{"slug": slug} for slug in obj.segments]

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

    def get_firefoxLabsDescriptionLinks(self, obj):
        if obj.firefox_labs_description_links:
            with contextlib.suppress(json.JSONDecodeError):
                return json.loads(obj.firefox_labs_description_links)
