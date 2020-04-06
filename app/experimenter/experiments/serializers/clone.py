from rest_framework import serializers
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import Q

from experimenter.experiments.models import Experiment


class ExperimentCloneSerializer(serializers.ModelSerializer):
    clone_url = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("name", "clone_url")

    def validate_name(self, value):
        existing_slug_or_name = Experiment.objects.filter(
            Q(slug=slugify(value)) | Q(name=value)
        )

        if existing_slug_or_name:
            raise serializers.ValidationError("This experiment name already exists.")

        if slugify(value):
            return value
        else:
            raise serializers.ValidationError("That's an invalid name.")

    def get_clone_url(self, obj):
        return reverse("experiments-detail", kwargs={"slug": obj.slug})

    def update(self, instance, validated_data):
        user = self.context["request"].user
        name = validated_data.get("name")

        return instance.clone(name, user)
