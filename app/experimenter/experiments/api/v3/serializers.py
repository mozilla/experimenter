from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers

from experimenter.experiments.models import Experiment


class ExperimentRapidSerializer(serializers.ModelSerializer):
    type = serializers.HiddenField(default=Experiment.TYPE_RAPID)
    rapid_type = serializers.HiddenField(default=Experiment.RAPID_AA_CFR)
    owner = serializers.SlugRelatedField(
        slug_field="email", queryset=get_user_model().objects.all(), required=False
    )
    slug = serializers.CharField(max_length=255, required=False)

    class Meta:
        model = Experiment
        fields = (
            "type",
            "rapid_type",
            "owner",
            "name",
            "slug",
            "objectives",
        )

    def validate(self, data):
        if not self.instance:
            data["slug"] = slugify(self.initial_data["name"])
            data["owner"] = self.context["request"].user

        return data
