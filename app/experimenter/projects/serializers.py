from rest_framework import serializers

from experimenter.projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("slug",)
