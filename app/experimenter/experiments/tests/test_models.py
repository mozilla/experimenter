import datetime
import os.path
from decimal import Decimal

import mock
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.test import TestCase, override_settings
from django.utils import timezone
from parameterized import parameterized_class
from parameterized.parameterized import parameterized

from experimenter.base import UploadsStorage
from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchScreenshot,
    NimbusBucketRange,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
)
from experimenter.experiments.tests import JEXLParser
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusBucketRangeFactory,
    NimbusChangeLogFactory,
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusIsolationGroupFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentManager(TestCase):
    def test_sorted_by_latest_change(self):
        older_experiment = NimbusExperimentFactory.create()
        newer_experiment = NimbusExperimentFactory.create()

        NimbusChangeLogFactory.create(
            experiment=older_experiment, changed_on=datetime.datetime(2021, 1, 1)
        )
        NimbusChangeLogFactory.create(
            experiment=newer_experiment, changed_on=datetime.datetime(2021, 1, 2)
        )

        self.assertEqual(
            list(NimbusExperiment.objects.latest_changed()),
            [newer_experiment, older_experiment],
        )

    def test_launch_queue_returns_queued_experiments_with_correct_application(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.FENIX,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertEqual(
            list(
                NimbusExperiment.objects.launch_queue(
                    [NimbusExperiment.Application.DESKTOP]
                )
            ),
            [experiment1],
        )

    def test_end_queue_returns_ending_experiments_with_correct_application(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            application=NimbusExperiment.Application.FENIX,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_REJECT,
            status_next=NimbusExperiment.Status.COMPLETE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertEqual(
            list(
                NimbusExperiment.objects.end_queue([NimbusExperiment.Application.DESKTOP])
            ),
            [experiment1],
        )

    def test_update_queue_returns_experiments_that_should_update_by_application(self):
        # Should update, correct application
        experiment_should_update = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        # Should update, but wrong application
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE,
            application=NimbusExperiment.Application.FENIX,
        )

        # Shouldn't update, correct application
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.assertEqual(
            list(
                NimbusExperiment.objects.update_queue(
                    [NimbusExperiment.Application.DESKTOP]
                )
            ),
            [experiment_should_update],
        )

    def test_waiting_returns_any_waiting_experiments(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.IOS,
        )
        desktop_live_waiting = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertEqual(
            list(
                NimbusExperiment.objects.waiting([NimbusExperiment.Application.DESKTOP])
            ),
            [desktop_live_waiting],
        )

    def test_waiting_to_launch_only_returns_launching_experiments(self):
        launching = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            name="launching",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            name="created",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            name="launch approve approve",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            name="ending approve waiting",
        )

        self.assertEqual(
            list(
                NimbusExperiment.objects.waiting_to_launch_queue([launching.application])
            ),
            [launching],
        )

    def test_waiting_to_update_only_returns_updating_experiments(self):
        application = NimbusExperiment.Application.DESKTOP

        pausing = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=application,
            name="pausing",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            name="created",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=application,
            name="launch approve approve",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=application,
            name="ending approve waiting",
        )

        self.assertEqual(
            list(NimbusExperiment.objects.waiting_to_update_queue([application])),
            [pausing],
        )


class TestNimbusExperiment(TestCase):
    def test_str(self):
        experiment = NimbusExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(str(experiment), experiment.name)

    def test_targeting_for_experiment_without_channels(self):
        experiment = NimbusExperimentFactory.create(
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_95,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting,
            (
                "(os.isMac) "
                "&& ('app.shield.optoutstudies.enabled'|preferenceValue) "
                "&& (version|versionCompare('83.!') >= 0) "
                "&& (version|versionCompare('95.*') <= 0)"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_empty_targeting_for_mobile(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(experiment.targeting, "true")
        JEXLParser().parse(experiment.targeting)

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Version.FIREFOX_97),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_97,
            ),
            (NimbusExperiment.Application.IOS, NimbusExperiment.Version.FIREFOX_97),
            (NimbusExperiment.Application.FOCUS_IOS, NimbusExperiment.Version.FIREFOX_96),
        ]
    )
    def test_targeting_omits_version_for_unsupported_clients(self, application, version):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=application,
            firefox_min_version=version,
            firefox_max_version=version,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(experiment.targeting, "true")

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Version.FIREFOX_98),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_98,
            ),
            (NimbusExperiment.Application.IOS, NimbusExperiment.Version.FIREFOX_98),
            (NimbusExperiment.Application.FOCUS_IOS, NimbusExperiment.Version.FIREFOX_97),
        ]
    )
    def test_targeting_includes_min_version_for_supported_clients(
        self, application, version
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=application,
            firefox_min_version=version,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting, f"(app_version|versionCompare('{version}') >= 0)"
        )

    def test_targeting_min_version_check_supports_semver_comparison(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting, "(app_version|versionCompare('100.!') >= 0)"
        )

    def test_targeting_max_version_check_supports_semver_comparison(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_100,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting, "(app_version|versionCompare('100.*') <= 0)"
        )

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Version.FIREFOX_98),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_98,
            ),
            (NimbusExperiment.Application.IOS, NimbusExperiment.Version.FIREFOX_98),
            (NimbusExperiment.Application.FOCUS_IOS, NimbusExperiment.Version.FIREFOX_97),
        ]
    )
    def test_targeting_includes_max_version_for_supported_clients(
        self, application, version
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=application,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=version,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting,
            f"(app_version|versionCompare('{version.replace('!', '*')}') <= 0)",
        )

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Version.FIREFOX_98),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_98,
            ),
            (NimbusExperiment.Application.IOS, NimbusExperiment.Version.FIREFOX_98),
            (NimbusExperiment.Application.FOCUS_IOS, NimbusExperiment.Version.FIREFOX_97),
        ]
    )
    def test_targeting_includes_min_and_max_version_for_supported_clients(
        self, application, version
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=application,
            firefox_min_version=version,
            firefox_max_version=version,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting,
            f"(app_version|versionCompare('{version}') >= 0) "
            f"&& (app_version|versionCompare('{version.replace('!', '*')}') <= 0)",
        )

    def test_targeting_without_firefox_min_version(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_95,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NIGHTLY,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting,
            (
                "(os.isMac) "
                '&& (browserSettings.update.channel == "nightly") '
                "&& ('app.shield.optoutstudies.enabled'|preferenceValue) "
                "&& (version|versionCompare('95.*') <= 0)"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_without_firefox_max_version(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NIGHTLY,
            locales=[],
            countries=[],
            languages=[],
        )

        self.assertEqual(
            experiment.targeting,
            (
                "(os.isMac) "
                '&& (browserSettings.update.channel == "nightly") '
                "&& ('app.shield.optoutstudies.enabled'|preferenceValue) "
                "&& (version|versionCompare('83.!') >= 0)"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_without_channel_version(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[],
            languages=[],
        )
        self.assertEqual(
            experiment.targeting,
            "(os.isMac) && ('app.shield.optoutstudies.enabled'|preferenceValue)",
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_locales(self):
        locale_ca = LocaleFactory.create(code="en-CA")
        locale_us = LocaleFactory.create(code="en-US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[locale_ca, locale_us],
            countries=[],
            languages=[],
        )
        self.assertEqual(
            experiment.targeting,
            (
                "(os.isMac) "
                "&& ('app.shield.optoutstudies.enabled'|preferenceValue) "
                "&& (locale in ['en-CA', 'en-US'])"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_countries(self):
        country_ca = CountryFactory.create(code="CA")
        country_us = CountryFactory.create(code="US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[],
            countries=[country_ca, country_us],
            languages=[],
        )
        self.assertEqual(
            experiment.targeting,
            (
                "(os.isMac) "
                "&& ('app.shield.optoutstudies.enabled'|preferenceValue) "
                "&& (region in ['CA', 'US'])"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_locales_and_countries_desktop(self):
        locale_ca = LocaleFactory.create(code="en-CA")
        locale_us = LocaleFactory.create(code="en-US")
        country_ca = CountryFactory.create(code="CA")
        country_us = CountryFactory.create(code="US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[locale_ca, locale_us],
            countries=[country_ca, country_us],
            languages=[],
        )
        self.assertEqual(
            experiment.targeting,
            (
                "(os.isMac) "
                "&& ('app.shield.optoutstudies.enabled'|preferenceValue) "
                "&& (locale in ['en-CA', 'en-US']) "
                "&& (region in ['CA', 'US'])"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_languages_mobile(self):
        language_en = LanguageFactory.create(code="en")
        language_fr = LanguageFactory.create(code="fr")
        language_es = LanguageFactory.create(code="es")
        targeting_config = NimbusExperiment.TargetingConfig
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=targeting_config.MOBILE_NEW_USERS,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            languages=[language_en, language_es, language_fr],
        )
        self.assertEqual(
            experiment.targeting,
            (
                "(is_already_enrolled || days_since_install < 7) "
                "&& (language in ['en', 'es', 'fr'])"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    # TODO: Remove once UI for mobile get relased to support languages
    def test_targeting_with_locales_languages_mobile(self):
        locale_ca = LocaleFactory.create(code="en-CA")
        locale_us = LocaleFactory.create(code="en-US")
        locale_ro = LocaleFactory.create(code="ro")
        locale_de = LocaleFactory.create(code="de")
        locale_es = LocaleFactory.create(code="es-ES")
        language_en = LanguageFactory.create(code="en")
        language_fr = LanguageFactory.create(code="fr")
        language_es = LanguageFactory.create(code="es")
        targeting_config = NimbusExperiment.TargetingConfig
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=targeting_config.MOBILE_NEW_USERS,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            locales=[locale_ca, locale_ro, locale_de, locale_es, locale_us],
            languages=[language_en, language_es, language_fr],
        )
        self.assertEqual(
            experiment.targeting,
            (
                "(is_already_enrolled || days_since_install < 7) "
                "&& ('de' in locale || 'en' in locale || 'es' in locale "
                "|| 'ro' in locale) "
                "&& (language in ['en', 'es', 'fr'])"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_uses_published_targeting_string(self):
        published_targeting = "published targeting jexl"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            published_dto={"targeting": published_targeting},
        )
        self.assertEqual(experiment.targeting, published_targeting)

    def test_targeting_with_missing_published_targeting(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            published_dto={"other_field": "some value"},
        )
        self.assertEqual(
            experiment.targeting, NimbusExperiment.PUBLISHED_TARGETING_MISSING
        )

    def test_targeting_config_returns_config_with_valid_slug(self):
        experiment = NimbusExperimentFactory.create(
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING
        )
        self.assertEqual(
            experiment.targeting_config,
            NimbusExperiment.TARGETING_CONFIGS[
                NimbusExperiment.TargetingConfig.NO_TARGETING
            ],
        )

    def test_targeting_config_returns_None_with_invalid_slug(self):
        experiment = NimbusExperimentFactory.create(targeting_config_slug="invalid slug")
        self.assertIsNone(experiment.targeting_config)

    def test_start_date_returns_None_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.start_date)

    def test_end_date_returns_None_for_not_ended_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.end_date)

    def test_start_date_returns_datetime_for_started_experiment(self):
        experiment = NimbusExperimentFactory.create()
        start_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        )
        self.assertEqual(experiment.start_date, start_change.changed_on.date())

    def test_launch_month_returns_month_for_started_experiment(self):
        experiment = NimbusExperimentFactory.create()
        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=timezone.now() + datetime.timedelta(days=1),
        )
        self.assertEqual(experiment.launch_month, experiment.start_date.strftime("%B"))

    def test_start_date_uses_most_recent_start_change(self):
        experiment = NimbusExperimentFactory.create()
        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=timezone.now() + datetime.timedelta(days=1),
        )
        start_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=timezone.now() + datetime.timedelta(days=2),
        )
        self.assertEqual(experiment.start_date, start_change.changed_on.date())

    def test_end_date_returns_datetime_for_ended_experiment(self):
        experiment = NimbusExperimentFactory.create()
        end_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        )
        self.assertEqual(experiment.end_date, end_change.changed_on.date())

    def test_enrollment_duration_for_ended_experiment(self):
        experiment = NimbusExperimentFactory.create()
        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=timezone.now() + datetime.timedelta(days=1),
        )
        expected_enrollment_duration = (
            experiment.start_date.strftime("%Y-%m-%d")
            + " to "
            + experiment.computed_end_date.strftime("%Y-%m-%d")
        )
        self.assertEqual(experiment.enrollment_duration, expected_enrollment_duration)

    def test_enrollment_duration_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        self.assertEqual(experiment.enrollment_duration, experiment.proposed_duration)

    def test_end_date_uses_most_recent_end_change(self):
        experiment = NimbusExperimentFactory.create()
        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=timezone.now() + datetime.timedelta(days=1),
        )
        end_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=timezone.now() + datetime.timedelta(days=2),
        )
        self.assertEqual(experiment.end_date, end_change.changed_on.date())

    def test_proposed_end_date_returns_None_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.proposed_end_date)

    def test_proposed_end_date_returns_start_date_plus_duration(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
            with_latest_change_now=True,
        )
        self.assertEqual(
            experiment.proposed_end_date,
            datetime.date.today() + datetime.timedelta(days=10),
        )

    def test_should_end_returns_False_before_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
            with_latest_change_now=True,
        )
        self.assertFalse(experiment.should_end)

    def test_should_end_returns_True_after_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))
        self.assertTrue(experiment.should_end)

    def test_should_end_enrollment_returns_False_before_proposed_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            with_latest_change_now=True,
        )
        self.assertFalse(experiment.should_end_enrollment)

    def test_should_end_enrollment_returns_True_after_proposed_enrollment_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))
        self.assertTrue(experiment.should_end_enrollment)

    def test_computed_enrollment_days_returns_changed_on_minus_start_date(self):
        expected_days = 3
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_APPROVE,
        )

        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(
            changed_on=datetime.datetime.now() - datetime.timedelta(days=expected_days)
        )

        experiment.changes.filter(experiment_data__is_paused=True).update(
            changed_on=datetime.datetime.now()
        )

        self.assertEqual(
            experiment.computed_enrollment_days,
            expected_days,
        )

    def test_computed_enrollment_days_uses_end_date_without_pause(self):
        expected_days = 5
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE_WITHOUT_PAUSE,
            proposed_enrollment=99,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(
            changed_on=datetime.datetime.now() - datetime.timedelta(days=expected_days)
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        ).update(changed_on=datetime.datetime.now())
        self.assertEqual(
            experiment.computed_enrollment_days,
            expected_days,
        )

    def test_computed_enrollment_days_returns_fallback(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        self.assertEqual(
            experiment.computed_enrollment_days,
            experiment.proposed_enrollment,
        )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PAUSING_REVIEW_REQUESTED,),
            (NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,),
        ]
    )
    def test_computed_enrollment_days_returns_fallback_while_pause_pending_approval(
        self, lifecycle
    ):
        expected_days = 99
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            proposed_enrollment=expected_days,
        )
        # Set the span to 5 days, but that shouldn't apply while pending approval
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=5))
        experiment.changes.filter(experiment_data__is_paused=True).update(
            changed_on=datetime.datetime.now()
        )
        self.assertEqual(
            experiment.computed_enrollment_days,
            expected_days,
        )

    def test_computed_duration_days_returns_computed_end_date_minus_start_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            proposed_duration=10,
        )

        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=7))

        experiment.changes.filter(
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        ).update(changed_on=datetime.datetime.now())

        self.assertEqual(
            experiment.computed_duration_days,
            7,
        )

    def test_computed_duration_days_returns_fallback(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        self.assertEqual(
            experiment.computed_duration_days,
            experiment.proposed_duration,
        )

    def test_computed_end_date_returns_proposed(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
        )

        self.assertEqual(
            experiment.computed_end_date,
            experiment.proposed_end_date,
        )

    def test_computed_end_date_returns_actual(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )

        self.assertEqual(
            experiment.computed_end_date,
            experiment.end_date,
        )

    def test_monitoring_dashboard_url_is_when_experiment_not_begun(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.DRAFT,
        )

        from_date = datetime.date.today() - datetime.timedelta(days=1)
        to_date = datetime.date.today() + datetime.timedelta(days=1)

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.slug,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
            ),
        )

    def test_monitoring_dashboard_url_returns_url_when_experiment_has_begun(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.LIVE,
        )

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )

        from_date = datetime.date(2019, 4, 30)
        to_date = datetime.date.today() + datetime.timedelta(days=1)

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.slug,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
            ),
        )

    def test_monitoring_dashboard_url_returns_url_when_experiment_is_complete(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.COMPLETE,
        )

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=datetime.date(2019, 5, 10),
        )

        from_date = datetime.date(2019, 4, 30)
        to_date = datetime.date(2019, 5, 12)

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.slug,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
            ),
        )

    def test_review_url_should_return_simple_review_url(self):
        with override_settings(
            KINTO_ADMIN_URL="https://settings-writer.stage.mozaws.net/v1/admin/",
        ):
            expected = "https://settings-writer.stage.mozaws.net/v1/admin/#/buckets/main-workspace/collections/nimbus-desktop-experiments/simple-review"  # noqa E501
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
                application=NimbusExperiment.Application.DESKTOP,
            )
            self.assertEqual(experiment.review_url, expected)

    def test_review_url_stage_should_return_simple_review_url_without_slash(self):
        with override_settings(
            KINTO_ADMIN_URL="http://localhost:8888/v1/admin",
        ):
            expected = "http://localhost:8888/v1/admin#/buckets/main-workspace/collections/nimbus-desktop-experiments/simple-review"  # noqa E501
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
                application=NimbusExperiment.Application.DESKTOP,
            )
            self.assertEqual(experiment.review_url, expected)

    def test_clear_branches_deletes_branches_without_deleting_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNotNone(experiment.reference_branch)
        self.assertEqual(experiment.branches.count(), 2)
        self.assertEqual(experiment.changes.count(), 1)

        experiment.delete_branches()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertIsNone(experiment.reference_branch)
        self.assertEqual(experiment.branches.count(), 0)
        self.assertEqual(experiment.changes.count(), 1)

    def test_allocate_buckets_generates_bucket_range(self):
        feature = NimbusFeatureConfigFactory(slug="feature")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
            population_percent=Decimal("50.0"),
        )
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 5000)
        self.assertEqual(
            experiment.bucket_range.isolation_group.name,
            "firefox-desktop-feature-release",
        )

    def test_allocate_buckets_creates_new_bucket_range_if_population_changes(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, population_percent=Decimal("50.0")
        )
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 5000)

        experiment.population_percent = Decimal("20.0")
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 2000)

    def test_allocate_buckets_deletes_buckets_and_empty_isolation_group(self):
        feature = NimbusFeatureConfigFactory(slug="feature")

        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
            population_percent=Decimal("50.0"),
        )
        experiment1.allocate_bucket_range()

        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
            population_percent=Decimal("100.0"),
        )
        experiment2.allocate_bucket_range()

        self.assertEqual(NimbusBucketRange.objects.count(), 2)
        self.assertEqual(NimbusIsolationGroup.objects.count(), 2)

        experiment2.population_percent = Decimal("50.0")
        experiment2.save()
        experiment2.allocate_bucket_range()

        self.assertEqual(NimbusBucketRange.objects.count(), 2)
        self.assertEqual(NimbusIsolationGroup.objects.count(), 1)

    def test_allocate_buckets_deletes_buckets_preserves_occupied_isolation_group(self):
        feature = NimbusFeatureConfigFactory(slug="feature")

        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
            population_percent=Decimal("50.0"),
        )
        experiment1.allocate_bucket_range()

        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
            population_percent=Decimal("25.0"),
        )
        experiment2.allocate_bucket_range()

        self.assertEqual(NimbusBucketRange.objects.count(), 2)
        self.assertEqual(NimbusIsolationGroup.objects.count(), 1)

        experiment2.population_percent = Decimal("30.0")
        experiment2.save()
        experiment2.allocate_bucket_range()

        self.assertEqual(NimbusBucketRange.objects.count(), 2)
        self.assertEqual(NimbusIsolationGroup.objects.count(), 1)

    def test_bucket_namespace_changes_for_rollout(self):
        feature = NimbusFeatureConfigFactory(slug="feature")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
            population_percent=Decimal("50.0"),
        )
        original_namespace = experiment.bucket_namespace

        experiment.is_rollout = True
        experiment.save()

        self.assertNotEqual(original_namespace, experiment.bucket_namespace)
        self.assertEqual(
            experiment.bucket_namespace,
            "firefox-desktop-feature-release-rollout",
        )

    def test_proposed_enrollment_end_date_without_start_date_is_None(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.proposed_enrollment_end_date)

    def test_proposed_enrollment_end_date_with_start_date_returns_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            with_latest_change_now=True,
        )
        self.assertEqual(
            experiment.proposed_enrollment_end_date,
            datetime.date.today() + datetime.timedelta(days=10),
        )

    def test_can_review_false_for_requesting_user(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertFalse(experiment.can_review(experiment.owner))

    @parameterized.expand(
        (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
        )
    )
    def test_can_review_true_for_non_requesting_user(self, last_publish_status):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            generate_nimbus_changelog(experiment, experiment.owner, "test message")
            if publish_status == last_publish_status:
                break

        self.assertTrue(experiment.can_review(UserFactory.create()))

    def test_results_ready_true(self):
        experiment = NimbusExperimentFactory.create()

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )
        self.assertTrue(experiment.results_ready)

    def test_results_ready_false(self):
        experiment = NimbusExperimentFactory.create()

        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date.today() - datetime.timedelta(days=2),
        )
        self.assertFalse(experiment.results_ready)

    @parameterized.expand(
        [
            (True, NimbusExperimentFactory.Lifecycles.CREATED),
            (False, NimbusExperimentFactory.Lifecycles.PREVIEW),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE),
        ]
    )
    def test_can_edit(self, expected_can_edit, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        self.assertEqual(experiment.can_edit, expected_can_edit)

    @parameterized.expand(
        [
            (True, NimbusExperimentFactory.Lifecycles.CREATED),
            (False, NimbusExperimentFactory.Lifecycles.PREVIEW),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE),
            (True, NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE),
        ]
    )
    def test_can_archive(self, expected_can_archive, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        self.assertEqual(experiment.can_archive, expected_can_archive)

    @parameterized.expand([(settings.DEV_USER_EMAIL, True), ("jdoe@mozilla.org", False)])
    @override_settings(SKIP_REVIEW_ACCESS_CONTROL_FOR_DEV_USER=True)
    def test_can_review_for_requesting_user_if_dev_user_and_setting_enabled(
        self, email, is_allowed
    ):
        user = UserFactory.create(email=email)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            owner=user,
        )
        experiment.apply_lifecycle_state(
            NimbusExperimentFactory.LifecycleStates.DRAFT_REVIEW
        )
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertEqual(experiment.can_review(user), is_allowed)

    def test_can_review_false_for_non_review_publish_status(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        experiment.apply_lifecycle_state(
            NimbusExperimentFactory.LifecycleStates.DRAFT_REVIEW
        )
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE

        experiment.save()

        self.assertFalse(experiment.can_review(UserFactory.create()))

    @parameterized.expand(
        [
            (
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_TIMEOUT,
            ),
            (
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_TIMEOUT,
            ),
        ]
    )
    def test_timeout_changelog_for_timedout_publish_flow(
        self, lifecycle_start, lifecycle_waiting, lifecycle_timeout
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle_start)

        # Simulate waiting for approval in remote settings
        experiment.apply_lifecycle_state(lifecycle_waiting.value[-1])
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        # No timeout at first.
        self.assertIsNone(experiment.changes.latest_timeout())

        # Next, simulate a timeout.
        experiment.apply_lifecycle_state(lifecycle_timeout.value[-1])
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        # Timeout should be the latest changelog entry.
        self.assertEqual(
            experiment.changes.latest_timeout(), experiment.changes.latest_change()
        )

    def test_has_state_true(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
        )
        self.assertTrue(
            experiment.has_filter(
                Q(
                    status=NimbusExperiment.Status.DRAFT,
                    publish_status=NimbusExperiment.PublishStatus.WAITING,
                )
            )
        )

    def test_has_state_false(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
        )
        self.assertFalse(
            experiment.has_filter(
                Q(
                    status=NimbusExperiment.Status.DRAFT,
                    publish_status=NimbusExperiment.PublishStatus.IDLE,
                )
            )
        )

    @parameterized.expand(
        [
            [False, False, False, False, False],
            [True, False, False, True, False],
            [False, True, False, True, True],
            [False, False, True, True, True],
        ]
    )
    def test_signoff_recommendations(
        self,
        risk_brand,
        risk_revenue,
        risk_partner_related,
        vp_recommended,
        legal_recommended,
    ):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            risk_brand=risk_brand,
            risk_revenue=risk_revenue,
            risk_partner_related=risk_partner_related,
        )
        self.assertEqual(experiment.signoff_recommendations["qa_signoff"], True)
        self.assertEqual(experiment.signoff_recommendations["vp_signoff"], vp_recommended)
        self.assertEqual(
            experiment.signoff_recommendations["legal_signoff"], legal_recommended
        )

    @parameterized.expand(
        [
            [False, 60, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING],
            [False, 60, NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING],
            [False, 60, NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING],
            [True, 0, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING],
            [True, 0, NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING],
            [True, 0, NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING],
        ]
    )
    def test_should_timeout(self, expected, timeout, lifecycle):
        with override_settings(KINTO_REVIEW_TIMEOUT=timeout):
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle, with_latest_change_now=True
            )
            self.assertEqual(experiment.should_timeout, expected)

    def test_clone_created_experiment(self):
        owner = UserFactory.create()
        parent = NimbusExperiment.objects.create(
            owner=owner,
            name="Parent Experiment",
            slug="parent-experiment",
            application=NimbusExperiment.Application.DESKTOP,
            conclusion_recommendation="RERUN",
            takeaways_summary="takeaway",
        )
        child = self._clone_experiment_and_assert_common_expectations(parent)

        # Specifically assert default values for a clone of a newly-created experiment
        self.assertEqual(child.public_description, "")
        self.assertEqual(child.risk_mitigation_link, "")
        self.assertEqual(
            child.proposed_duration, NimbusExperiment.DEFAULT_PROPOSED_DURATION
        )
        self.assertEqual(
            child.proposed_enrollment, NimbusExperiment.DEFAULT_PROPOSED_ENROLLMENT
        )
        self.assertEqual(child.population_percent, 0)
        self.assertEqual(child.total_enrolled_clients, 0)
        self.assertEqual(child.firefox_min_version, NimbusExperiment.Version.NO_VERSION)
        self.assertEqual(child.firefox_max_version, NimbusExperiment.Version.NO_VERSION)
        self.assertEqual(child.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(child.channel, NimbusExperiment.Channel.NO_CHANNEL)
        self.assertEqual(child.hypothesis, NimbusExperiment.HYPOTHESIS_DEFAULT)
        self.assertEqual(child.primary_outcomes, [])
        self.assertEqual(child.secondary_outcomes, [])
        self.assertEqual(child.feature_configs.count(), 0)
        self.assertEqual(
            child.targeting_config_slug, NimbusExperiment.TargetingConfig.NO_TARGETING
        )
        self.assertIsNone(child.reference_branch)
        self.assertIsNone(child.published_dto)
        self.assertIsNone(child.results_data)
        self.assertFalse(child.risk_partner_related)
        self.assertFalse(child.risk_revenue)
        self.assertFalse(child.risk_brand)
        self.assertFalse(NimbusBucketRange.objects.filter(experiment=child).exists())
        self.assertEqual(child.locales.all().count(), 0)
        self.assertEqual(child.countries.all().count(), 0)
        self.assertEqual(child.branches.all().count(), 0)
        self.assertEqual(child.changes.all().count(), 1)
        self.assertIsNone(child.conclusion_recommendation)
        self.assertIsNone(child.takeaways_summary)

    def test_clone_completed_experiment(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        self._clone_experiment_and_assert_common_expectations(parent)

    def test_clone_archived_experiment(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        parent.is_archived = True
        generate_nimbus_changelog(parent, parent.owner, "Archiving experiment")
        self._clone_experiment_and_assert_common_expectations(parent)

    def test_clone_with_rollout_branch_slug(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        rollout_branch = parent.branches.first()
        self._clone_experiment_and_assert_common_expectations(parent, rollout_branch.slug)

    def test_clone_with_rollout_branch_slug_invalid(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        with self.assertRaises(NimbusBranch.DoesNotExist):
            self._clone_experiment_and_assert_common_expectations(parent, "BAD SLUG")

    def _clone_experiment_and_assert_common_expectations(
        self, parent, rollout_branch_slug=None
    ):
        child = parent.clone("Child Experiment", parent.owner, rollout_branch_slug)

        self.assertEqual(child.parent, parent)
        self.assertFalse(child.is_archived)
        self.assertEqual(child.owner, parent.owner)
        self.assertEqual(child.status, NimbusExperiment.Status.DRAFT)
        self.assertIsNone(child.status_next)
        self.assertEqual(child.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(child.name, "Child Experiment")
        self.assertEqual(child.slug, "child-experiment")
        self.assertFalse(child.is_paused)
        self.assertEqual(child.public_description, parent.public_description)
        self.assertEqual(child.application, parent.application)
        self.assertEqual(child.channel, parent.channel)
        self.assertEqual(child.hypothesis, parent.hypothesis)
        self.assertEqual(child.firefox_min_version, parent.firefox_min_version)
        self.assertEqual(child.firefox_max_version, parent.firefox_max_version)
        self.assertEqual(child.risk_mitigation_link, parent.risk_mitigation_link)
        self.assertEqual(child.primary_outcomes, parent.primary_outcomes)
        self.assertEqual(child.secondary_outcomes, parent.secondary_outcomes)

        self.assertEqual(child.targeting_config_slug, parent.targeting_config_slug)
        self.assertIsNone(child.published_dto)
        self.assertIsNone(child.results_data)
        self.assertEqual(child.risk_partner_related, parent.risk_partner_related)
        self.assertEqual(child.risk_revenue, parent.risk_revenue)
        self.assertEqual(child.risk_brand, parent.risk_brand)
        self.assertFalse(NimbusBucketRange.objects.filter(experiment=child).exists())
        self.assertEqual(
            set(child.feature_configs.all().values_list("slug", flat=True)),
            set(parent.feature_configs.all().values_list("slug", flat=True)),
        )
        self.assertEqual(
            set(child.locales.all().values_list("code", flat=True)),
            set(parent.locales.all().values_list("code", flat=True)),
        )
        self.assertEqual(
            set(child.countries.all().values_list("code", flat=True)),
            set(parent.countries.all().values_list("code", flat=True)),
        )

        for parent_link in parent.documentation_links.all():
            child_link = child.documentation_links.get(title=parent_link.title)
            self.assertEqual(child_link.link, parent_link.link)

        self.assertEqual(child.changes.all().count(), 1)

        if rollout_branch_slug:
            self.assertEqual(
                child.proposed_duration, NimbusExperiment.DEFAULT_PROPOSED_DURATION
            )
            self.assertEqual(
                child.proposed_enrollment, NimbusExperiment.DEFAULT_PROPOSED_ENROLLMENT
            )
            self.assertEqual(child.population_percent, 0)
            self.assertEqual(child.total_enrolled_clients, 0)

            self.assertEqual(child.branches.count(), 1)
            child_branch = child.branches.first()
            parent_branch = parent.branches.get(slug=rollout_branch_slug)

            self.assertEqual(child.reference_branch.id, child_branch.id)
            self.assertEqual(child.reference_branch.slug, child_branch.slug)

            self.assertEqual(child_branch.name, parent_branch.name)
            self.assertEqual(child_branch.description, parent_branch.description)
            self.assertEqual(child_branch.ratio, parent_branch.ratio)
            self.assertEqual(
                set(child_branch.feature_values.values_list("value", flat=True)),
                set(parent_branch.feature_values.values_list("value", flat=True)),
            )
        else:
            self.assertEqual(child.proposed_duration, parent.proposed_duration)
            self.assertEqual(child.proposed_enrollment, parent.proposed_enrollment)
            self.assertEqual(child.population_percent, parent.population_percent)
            self.assertEqual(child.total_enrolled_clients, parent.total_enrolled_clients)
            if parent.reference_branch:
                self.assertEqual(
                    child.reference_branch.slug, parent.reference_branch.slug
                )
                self.assertNotEqual(child.reference_branch.id, parent.reference_branch.id)

            for parent_branch in parent.branches.all():
                child_branch = child.branches.get(slug=parent_branch.slug)
                self.assertEqual(child_branch.name, parent_branch.name)
                self.assertEqual(child_branch.description, parent_branch.description)
                self.assertEqual(child_branch.ratio, parent_branch.ratio)
                self.assertEqual(
                    set(child_branch.feature_values.values_list("value", flat=True)),
                    set(parent_branch.feature_values.values_list("value", flat=True)),
                )
        return child


class TestNimbusBranch(TestCase):
    def test_str(self):
        experiment = NimbusExperimentFactory.create(name="experiment")
        branch = NimbusBranchFactory.create(experiment=experiment, name="branch")
        self.assertEqual(str(branch), "experiment: branch")


class TestNimbusDocumentLink(TestCase):
    def test_str(self):
        doco_link = NimbusDocumentationLinkFactory.create(
            title="doc", link="www.example.com"
        )
        self.assertEqual(str(doco_link), "doc (www.example.com)")


@parameterized_class(("application",), [list(NimbusExperiment.Application)])
class TestNimbusIsolationGroup(TestCase):
    def test_empty_isolation_group_creates_isolation_group_and_bucket_range(self):
        """
        Common case: A new empty isolation group for an experiment
        that is orthogonal to all other current experiments.  This will
        likely describe most experiment launches.
        """
        experiment = NimbusExperimentFactory.create(application=self.application)
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group.name, experiment.slug)
        self.assertEqual(bucket.isolation_group.instance, 1)
        self.assertEqual(bucket.isolation_group.total, NimbusExperiment.BUCKET_TOTAL)
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            experiment.application_config.randomization_unit,
        )

    def test_existing_isolation_group_adds_bucket_range(self):
        """
        Rare case: An isolation group with no buckets allocated already exists.
        This may become common when users can create their own isolation groups
        and then later assign experiments to them.
        """
        experiment = NimbusExperimentFactory.create(application=self.application)
        isolation_group = NimbusIsolationGroupFactory.create(
            name=experiment.slug, application=self.application
        )
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group, isolation_group)
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            experiment.application_config.randomization_unit,
        )

    def test_existing_isolation_group_with_buckets_adds_next_bucket_range(self):
        """
        Common case: An isolation group with experiment bucket allocations exists,
        and a subsequent bucket allocation is requested.  This will be the common case
        for any experiments that share an isolation group.
        """
        experiment = NimbusExperimentFactory.create(application=self.application)
        isolation_group = NimbusIsolationGroupFactory.create(
            name=experiment.slug, application=self.application
        )
        NimbusBucketRangeFactory.create(
            isolation_group=isolation_group, start=0, count=100
        )
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 100)
        self.assertEqual(bucket.end, 199)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group, isolation_group)
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            experiment.application_config.randomization_unit,
        )

    def test_full_isolation_group_creates_next_isolation_group_adds_bucket_range(
        self,
    ):
        """
        Rare case:  An isolation group with experiment bucket allocations exists, and the
        next requested bucket allocation would overflow its total bucket range, and so a
        an isolation group with the same name but subsequent instance ID is created.

        This is currently treated naively, ie does not account for possible collisions and
        overlaps.  When this case becomes more common this will likely need to be given
        more thought.
        """
        experiment = NimbusExperimentFactory.create(application=self.application)
        isolation_group = NimbusIsolationGroupFactory.create(
            name=experiment.slug, application=self.application, total=100
        )
        NimbusBucketRangeFactory(isolation_group=isolation_group, count=100)
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            experiment.slug, experiment, 100
        )
        self.assertEqual(bucket.start, 0)
        self.assertEqual(bucket.end, 99)
        self.assertEqual(bucket.count, 100)
        self.assertEqual(bucket.isolation_group.name, isolation_group.name)
        self.assertEqual(bucket.isolation_group.instance, isolation_group.instance + 1)
        self.assertEqual(
            bucket.isolation_group.randomization_unit,
            experiment.application_config.randomization_unit,
        )

    def test_existing_isolation_group_with_matching_name_but_not_application_is_filtered(
        self,
    ):
        """
        Now that isolation groups are bound to applications, we have to check for the
        case where isolation groups with the same name but different applications are
        treated separately.
        """
        name = "isolation group name"
        NimbusIsolationGroupFactory.create(
            name=name, application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create(
            name=name, slug=name, application=NimbusExperiment.Application.FENIX
        )
        bucket = NimbusIsolationGroup.request_isolation_group_buckets(
            name, experiment, 100
        )
        self.assertEqual(bucket.isolation_group.name, name)
        self.assertEqual(
            bucket.isolation_group.application, NimbusExperiment.Application.FENIX
        )


class TestNimbusChangeLogManager(TestCase):
    def test_latest_review_request_returns_none_for_no_review_request(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.changes.latest_review_request())

    def test_latest_review_request_returns_change_for_idle_to_review(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        change = generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertEqual(experiment.changes.latest_review_request(), change)

    def test_latest_review_request_returns_most_recent_review_request(self):
        reviewer = UserFactory()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.save()
        generate_nimbus_changelog(experiment, reviewer, "test message")

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        second_request = generate_nimbus_changelog(
            experiment, experiment.owner, "test message"
        )

        self.assertEqual(experiment.changes.latest_review_request(), second_request)

    def test_latest_rejection_returns_none_for_no_rejection(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.changes.latest_rejection())

    def test_latest_rejection_returns_rejection_for_review_to_idle(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        changes = []
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.IDLE,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            changes.append(
                generate_nimbus_changelog(experiment, experiment.owner, "test message")
            )

        self.assertEqual(experiment.changes.latest_review_request(), changes[0])
        self.assertEqual(experiment.changes.latest_rejection(), changes[1])

    def test_latest_rejection_returns_rejection_for_waiting_to_idle(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        changes = []
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
            NimbusExperiment.PublishStatus.IDLE,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            changes.append(
                generate_nimbus_changelog(experiment, experiment.owner, "test message")
            )

        self.assertEqual(experiment.changes.latest_review_request(), changes[0])
        self.assertEqual(experiment.changes.latest_rejection(), changes[3])

    def test_launch_to_live_is_not_considered_latest_rejection(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
        )

        experiment.status = NimbusExperiment.Status.LIVE
        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertIsNone(experiment.changes.latest_rejection())

    def test_stale_timeout_not_returned(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertIsNone(experiment.changes.latest_timeout())

    def test_stale_rejection_not_returned(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        for publish_status in (
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
            NimbusExperiment.PublishStatus.WAITING,
            NimbusExperiment.PublishStatus.IDLE,
            NimbusExperiment.PublishStatus.REVIEW,
            NimbusExperiment.PublishStatus.APPROVED,
        ):
            experiment.publish_status = publish_status
            experiment.save()
            generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertIsNone(experiment.changes.latest_rejection())


class TestNimbusChangeLog(TestCase):
    def test_uses_message_if_set(self):
        changelog = NimbusChangeLogFactory.create()
        self.assertEqual(str(changelog), changelog.message)

    def test_formats_str_if_no_message_set(self):
        now = timezone.now()
        user = UserFactory.create()
        changelog = NimbusChangeLogFactory.create(
            changed_by=user,
            changed_on=now,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.PREVIEW,
            message=None,
        )
        self.assertEqual(str(changelog), f"Draft > Preview by {user.email} on {now}")


class TestNimbusFeatureConfig(TestCase):
    @parameterized.expand(list(NimbusExperiment.Application))
    def test_no_feature_fixture_exists(self, application):
        application_config = NimbusExperiment.APPLICATION_CONFIGS[application]
        self.assertTrue(
            NimbusFeatureConfig.objects.filter(
                name__startswith="No Feature", application=application
            ).exists(),
            (
                f"A 'No Feature {application_config.name}' FeatureConfig fixture "
                "must be added in a migration.  See 0166_add_missing_feature_config "
                "for examples."
            ),
        )


class TestNimbusBranchScreenshot(TestCase):
    def setUp(self):
        self.experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.branch = self.experiment.branches.first()
        self.image = SimpleUploadedFile("Capture.PNG", b"this is not a real image")
        self.screenshot = NimbusBranchScreenshot(
            branch=self.branch, description="Test description", image=self.image
        )

    @mock.patch("experimenter.experiments.models.uuid4")
    def test_nimbus_branch_screenshot_upload_to(self, mock_uuid4):
        self.assertEqual(type(self.screenshot.image.storage), UploadsStorage)
        with mock.patch.object(self.screenshot.image.storage, "save") as mock_save:
            mock_uuid4.return_value = "predictable"
            mock_save.return_value = "saved/path/dontcare"
            expected_filename = os.path.join(
                self.experiment.slug, f"{mock_uuid4.return_value}.png"
            )
            max_length = NimbusBranchScreenshot._meta.get_field("image").max_length
            self.screenshot.save()
            mock_save.assert_called_with(
                expected_filename, self.image, max_length=max_length
            )

    @mock.patch("experimenter.experiments.models.uuid4")
    def test_nimbus_branch_screenshot_delete_previous_on_save_change(self, mock_uuid4):
        with mock.patch.object(self.screenshot.image.storage, "delete") as mock_delete:
            mock_uuid4.return_value = "predictable"
            expected_filename = os.path.join(
                self.experiment.slug, f"{mock_uuid4.return_value}.png"
            )
            self.screenshot.save()
            new_image = SimpleUploadedFile("Capture2.PNG", b"fake new image")
            self.screenshot.image = new_image
            self.screenshot.save()
            mock_delete.assert_called_with(expected_filename)

    @mock.patch("experimenter.experiments.models.uuid4")
    def test_nimbus_branch_screenshot_preserve_previous_on_save_without_change(
        self, mock_uuid4
    ):
        with mock.patch.object(self.screenshot.image.storage, "delete") as mock_delete:
            self.screenshot.save()
            mock_delete.reset_mock()
            self.description = "different screenshot"
            self.screenshot.save()
            mock_delete.assert_not_called()

    @mock.patch("experimenter.experiments.models.uuid4")
    def test_nimbus_branch_screenshot_delete(self, mock_uuid4):
        with mock.patch.object(self.screenshot.image.storage, "delete") as mock_delete:
            mock_uuid4.return_value = "predictable"
            expected_filename = os.path.join(
                self.experiment.slug, f"{mock_uuid4.return_value}.png"
            )
            self.screenshot.save()
            self.screenshot.delete()
            mock_delete.assert_called_with(expected_filename)
