from rest_framework import serializers

from mozilla_nimbus_shared import get_data

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentBucketRange,
)

NIMBUS_DATA = get_data()


class ExperimentRapidBranchesSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("slug", "ratio", "value")

    def get_value(self, obj):
        # placeholder value
        return None


class ExperimentBucketRangeSerializer(serializers.ModelSerializer):
    namespace = serializers.SlugRelatedField(read_only=True, slug_field="name")
    randomizationUnit = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentBucketRange
        fields = ("randomizationUnit", "namespace", "start", "count", "total")

    def get_randomizationUnit(self, obj):
        return NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"]["arguments"][
            "bucketConfig"
        ]["randomizationUnit"]

    def get_total(self, obj):
        return obj.namespace.total


class ExperimentRapidArgumentSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="normandy_slug")
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    active = serializers.ReadOnlyField(default=True)
    isEnrollmentPaused = serializers.ReadOnlyField(default=False)
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    bucketConfig = serializers.SerializerMethodField()
    startDate = serializers.SerializerMethodField()
    endDate = serializers.ReadOnlyField(default=None)
    branches = ExperimentRapidBranchesSerializer(many=True, source="variants")
    referenceBranch = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = (
            "slug",
            "userFacingName",
            "userFacingDescription",
            "active",
            "isEnrollmentPaused",
            "features",
            "proposedEnrollment",
            "bucketConfig",
            "startDate",
            "endDate",
            "branches",
            "referenceBranch",
        )

    def get_bucketConfig(self, obj):

        if hasattr(obj, "bucket"):
            return ExperimentBucketRangeSerializer(obj.bucket).data
        return {
            "randomizationUnit": "normandy_id",
            "namespace": "",
            "start": 0,
            "count": 0,
            "total": 10000,
        }

    def get_referenceBranch(self, obj):
        if obj.variants.count():
            control_branch = obj.variants.get(is_control=True)
            return control_branch.slug

    def get_startDate(self, obj):
        # placeholder value
        if obj.start_date:
            return obj.start_date.isoformat()


class ExperimentRapidRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="normandy_slug")
    arguments = ExperimentRapidArgumentSerializer(source="*")
    enabled = serializers.ReadOnlyField(default=True)
    filter_expression = serializers.SerializerMethodField()
    targeting = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("id", "arguments", "filter_expression", "enabled", "targeting")

    def get_filter_expression(self, obj):
        return NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"][
            "filter_expression"
        ].format(minFirefoxVersion=obj.firefox_min_version)

    def get_targeting(self, obj):
        if ExperimentBucketRange.objects.filter(experiment=obj).exists():
            bucket_range = ExperimentBucketRange.objects.get(experiment=obj)
            bucket_namespace = bucket_range.namespace.name
            bucket_start = bucket_range.start

            bucket_config = NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"][
                "arguments"
            ]["bucketConfig"]

            randomization_unit = bucket_config["randomizationUnit"]
            bucket_count = bucket_config["count"]
            bucket_total = bucket_config["total"]
            audience_targeting = NIMBUS_DATA["Audiences"][obj.audience]["targeting"]

            targeting_string = NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"][
                "preset"
            ]["targeting"]

            return targeting_string.format(
                bucketNamespace=bucket_namespace,
                bucketStart=bucket_start,
                randomizationUnit=randomization_unit,
                bucketCount=bucket_count,
                bucketTotal=bucket_total,
                audienceTargeting=audience_targeting,
            )
