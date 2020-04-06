from rest_framework import serializers
from experimenter.experiments.models import Locale, Country


class LocaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locale
        fields = ("code", "name")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("code", "name")
