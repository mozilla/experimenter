from rest_framework import serializers

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
)


class ExperimentRapidSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.email")

    class Meta:
        model = Experiment
        fields = (
            "audience",
            "bugzilla_url",
            "features",
            "name",
            "objectives",
            "owner",
            "public_description",
            "rapid_type",
            "slug",
            "status",
            "type",
        )


class ExperimentRapidBranchesSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("slug", "ratio", "value")

    def get_value(self, obj):
        # placeholder value
        return None


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
        return {
            "randomizationUnit": "normandy_id",
            "namespace": "",
            "start": 0,
            "count": 0,
            "total": 10000,
        }

    def get_referenceBranch(self, obj):
        control_branch = obj.variants.get(is_control=True)
        return control_branch.slug

    def get_startDate(self, obj):
        # placeholder value
        return obj.start_date.isoformat()


class ExperimentRapidRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="normandy_slug")
    arguments = ExperimentRapidArgumentSerializer(source="*")
    filter_expression = serializers.ReadOnlyField(source="audience")
    enabled = serializers.ReadOnlyField(default=True)

    class Meta:
        model = Experiment
        fields = ("id", "arguments", "filter_expression", "enabled")
