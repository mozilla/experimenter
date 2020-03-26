import datetime

from rest_framework import serializers
from experimenter.experiments.models import Experiment, Country, Locale
from experimenter.experiments.constants import ExperimentConstants

from experimenter.experiments.serializers.design import ChangelogSerializerMixin


class CountrySerializerMultiSelect(serializers.ModelSerializer):
    value = serializers.IntegerField(source="id")
    label = serializers.CharField(source="name")

    class Meta:
        model = Country
        fields = ("label", "value")


class LocaleSerializerMultiSelect(serializers.ModelSerializer):
    value = serializers.IntegerField(source="id")
    label = serializers.CharField(source="name")

    class Meta:
        model = Locale
        fields = ("label", "value")


class ExperimentTimelinePopSerializer(
    ChangelogSerializerMixin, serializers.ModelSerializer
):
    proposed_start_date = serializers.DateField(
        required=False, allow_null=True, default=None
    )
    proposed_duration = serializers.IntegerField(
        required=False, allow_null=True, default=None
    )
    proposed_enrollment = serializers.IntegerField(
        required=False, allow_null=True, default=None
    )
    rollout_playbook = serializers.ChoiceField(
        choices=ExperimentConstants.ROLLOUT_PLAYBOOK_CHOICES,
        required=False,
        allow_null=True,
        default=None,
        allow_blank=True,
    )
    population_percent = serializers.DecimalField(
        required=False,
        max_digits=7,
        decimal_places=4,
        max_value=100.0000,
        min_value=0,
        allow_null=True,
        default=None,
    )
    firefox_channel = serializers.ChoiceField(
        choices=ExperimentConstants.CHANNEL_CHOICES,
        required=False,
        allow_null=True,
        default=None,
        allow_blank=True,
    )
    firefox_min_version = serializers.ChoiceField(
        choices=ExperimentConstants.MIN_VERSION_CHOICES,
        required=False,
        allow_null=True,
        default=None,
        allow_blank=True,
    )
    firefox_max_version = serializers.ChoiceField(
        choices=ExperimentConstants.MAX_VERSION_CHOICES,
        required=False,
        allow_null=True,
        default=None,
        allow_blank=True,
    )
    locales = LocaleSerializerMultiSelect(
        many=True, required=False, allow_null=True, default=None
    )
    countries = CountrySerializerMultiSelect(
        many=True, required=False, allow_null=True, default=None
    )
    platform = serializers.ChoiceField(
        choices=ExperimentConstants.PLATFORM_CHOICES,
        required=False,
        allow_null=True,
        default=None,
        allow_blank=True,
    )
    client_matching = serializers.CharField(
        required=False, allow_null=True, default=None, allow_blank=True
    )

    class Meta:
        fields = (
            "proposed_start_date",
            "proposed_enrollment",
            "rollout_playbook",
            "proposed_duration",
            "population_percent",
            "firefox_channel",
            "firefox_min_version",
            "firefox_max_version",
            "locales",
            "countries",
            "platform",
            "client_matching",
        )
        model = Experiment

    def validate_proposed_start_date(self, value):
        if value and value < datetime.date.today():
            raise serializers.ValidationError(
                "The delivery start date must be no earlier than the current date."
            )

        return value

    def validate(self, data):
        data = super().validate(data)

        if data["proposed_enrollment"] and data["proposed_duration"]:
            if data["proposed_enrollment"] >= data["proposed_duration"]:
                raise serializers.ValidationError(
                    {
                        "proposed_enrollment": (
                            "Enrollment duration is optional,"
                            " but if set, must be lower than the delivery "
                            "duration. If enrollment duration is not "
                            "specified - users are enrolled for the"
                            "entire delivery."
                        )
                    }
                )

        if data["firefox_min_version"] and data["firefox_max_version"]:
            if data["firefox_min_version"] > data["firefox_max_version"]:
                raise serializers.ValidationError(
                    {
                        "firefox_max_version": (
                            "The max version must be larger "
                            "than or equal to the min version."
                        )
                    }
                )

        return data

    def update(self, instance, validated_data):
        countries_data = validated_data.pop("countries")
        locales_data = validated_data.pop("locales")

        instance = super().update(instance, validated_data)

        countries_list = []
        if len(countries_data) > 0:
            countries_list = [int(country["id"]) for country in countries_data]
        instance.countries.set(countries_list)

        locales_list = []
        if len(locales_data) > 0:
            locales_list = [int(locale["id"]) for locale in locales_data]
        instance.locales.set(locales_list)

        validated_data["countries"] = countries_list
        validated_data["locales"] = locales_list

        self.update_changelog(instance, validated_data)

        return instance
