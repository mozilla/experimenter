from rest_framework import serializers

from experimenter.base.models import Country, Locale


class LocaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locale
        fields = ("code", "name")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("code", "name")
