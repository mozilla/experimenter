import contextlib
import json

from django.conf import settings
from rest_framework import serializers

from experimenter.experiments.api.v6.serializers import NimbusBucketRangeSerializer
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusDocumentationLink,
    NimbusExperiment,
)


class NimbusDocumentationLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusDocumentationLink
        fields = ("title", "link")


class NimbusBranchSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    screenshots = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "features", "description", "screenshots")

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

    def get_screenshots(self, obj):
        return [s.image.url for s in obj.screenshots.all() if s.image and s.image.name]


class NimbusExperimentSerializer(serializers.ModelSerializer):
    schemaVersion = serializers.ReadOnlyField(default=settings.NIMBUS_SCHEMA_VERSION)
    id = serializers.ReadOnlyField(source="slug")
    arguments = serializers.ReadOnlyField(default={})
    application = serializers.SerializerMethodField()
    appName = serializers.SerializerMethodField()
    appId = serializers.SerializerMethodField()
    branches = NimbusBranchSerializer(many=True)
    channels = serializers.SerializerMethodField()
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
    locales = serializers.SerializerMethodField()
    localizations = serializers.SerializerMethodField()
    publishedDate = serializers.DateTimeField(source="published_date")
    documentationLinks = NimbusDocumentationLinkSerializer(
        source="documentation_links", many=True
    )

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
            "channels",
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
            "locales",
            "localizations",
            "publishedDate",
            "documentationLinks",
        )

    def get_application(self, obj):
        return self.get_appId(obj)

    def get_appName(self, obj):
        return obj.application_config.app_name

    def get_appId(self, obj):
        return obj.application_config.channel_app_id.get(obj.channel, "")

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

    def get_referenceBranch(self, obj):
        if obj.reference_branch:
            return obj.reference_branch.slug

    def get_localizations(self, obj):
        if obj.is_localized:
            try:
                return json.loads(obj.localizations)
            except json.decoder.JSONDecodeError:
                return None

    def get_locales(self, obj):
        locale_codes = [locale.code for locale in obj.locales.all()]
        if len(locale_codes):
            return locale_codes
