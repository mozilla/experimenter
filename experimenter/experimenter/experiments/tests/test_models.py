import datetime
from decimal import Decimal
from itertools import product
from pathlib import Path
from unittest import mock

import packaging
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
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
from experimenter.experiments.constants import ChangeEventType, NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchScreenshot,
    NimbusBucketRange,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
    NimbusFeatureConfig,
    NimbusFeatureVersion,
    NimbusIsolationGroup,
    NimbusVersionedSchema,
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
    NimbusVersionedSchemaFactory,
)
from experimenter.features import Features
from experimenter.features.tests import mock_valid_features
from experimenter.openidc.tests.factories import UserFactory
from experimenter.projects.tests.factories import ProjectFactory


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
    maxDiff = None

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
            projects=[],
        )

        self.assertEqual(
            experiment.targeting,
            (
                "(version|versionCompare('95.*') <= 0) "
                "&& (os.isMac) "
                "&& (version|versionCompare('83.!') >= 0)"
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
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_96,
            ),
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
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_97,
            ),
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
        JEXLParser().parse(experiment.targeting)

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
        JEXLParser().parse(experiment.targeting)

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
        JEXLParser().parse(experiment.targeting)

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Version.FIREFOX_98),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_98,
            ),
            (NimbusExperiment.Application.IOS, NimbusExperiment.Version.FIREFOX_98),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_97,
            ),
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
        JEXLParser().parse(experiment.targeting)

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Version.FIREFOX_98),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_98,
            ),
            (NimbusExperiment.Application.IOS, NimbusExperiment.Version.FIREFOX_98),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_97,
            ),
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
            (
                f"(app_version|versionCompare('{version.replace('!', '*')}') <= 0) "
                f"&& (app_version|versionCompare('{version}') >= 0)"
            ),
        )
        JEXLParser().parse(experiment.targeting)

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
                '(browserSettings.update.channel == "nightly") '
                "&& (version|versionCompare('95.*') <= 0) "
                "&& (os.isMac)"
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
                '(browserSettings.update.channel == "nightly") '
                "&& (os.isMac) "
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
            "(os.isMac)",
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
            ("(os.isMac) && (locale in ['en-CA', 'en-US'])"),
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
            ("(os.isMac) && (region in ['CA', 'US'])"),
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
                "&& (locale in ['en-CA', 'en-US']) "
                "&& (region in ['CA', 'US'])"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_languages_mobile(self):
        language_en = LanguageFactory.create(code="en")
        language_fr = LanguageFactory.create(code="fr")
        language_es = LanguageFactory.create(code="es")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            languages=[language_en, language_es, language_fr],
        )
        self.assertEqual(
            experiment.targeting,
            "(days_since_install < 7) && (language in ['en', 'es', 'fr'])",
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_projects(self):
        project_mdn = ProjectFactory.create(slug="mdn")

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            projects=[
                project_mdn,
            ],
        )
        for project in experiment.projects.all():
            self.assertEqual(
                {"slug": project.slug, "name": project.name},
                {"slug": project_mdn.slug, "name": project_mdn.name},
            )

    def test_targeting_with_sticky_desktop_experiment(self):
        locale_en = LocaleFactory.create(code="en")
        country_ca = CountryFactory.create(code="CA")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_101,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_ENTERPRISE_USERS,
            channel=NimbusExperiment.Channel.RELEASE,
            languages=[],
            locales=[locale_en],
            countries=[country_ca],
            is_sticky=True,
            is_rollout=False,
        )

        sticky_expression = (
            "("
            "(experiment.slug in activeExperiments) "
            "|| "
            "("
            "(!hasActiveEnterprisePolicies) "
            "&& "
            "(version|versionCompare('100.!') >= 0) "
            "&& (locale in ['en']) "
            "&& (region in ['CA'])"
            ")"
            ")"
        )
        self.assertEqual(
            experiment.targeting,
            (
                '(browserSettings.update.channel == "release") '
                "&& (version|versionCompare('101.*') <= 0) "
                f"&& {sticky_expression}"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_sticky_desktop_rollout(self):
        locale_en = LocaleFactory.create(code="en")
        country_ca = CountryFactory.create(code="CA")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_101,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_ENTERPRISE_USERS,
            channel=NimbusExperiment.Channel.RELEASE,
            languages=[],
            locales=[locale_en],
            countries=[country_ca],
            is_sticky=True,
            is_rollout=True,
        )

        sticky_expression = (
            "("
            "(experiment.slug in activeRollouts) "
            "|| "
            "("
            "(!hasActiveEnterprisePolicies) "
            "&& "
            "(version|versionCompare('100.!') >= 0) "
            "&& (locale in ['en']) "
            "&& (region in ['CA'])"
            ")"
            ")"
        )
        self.assertEqual(
            experiment.targeting,
            (
                '(browserSettings.update.channel == "release") '
                "&& (version|versionCompare('101.*') <= 0) "
                f"&& {sticky_expression}"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_sticky_mobile(self):
        language_en = LanguageFactory.create(code="en")
        country_ca = CountryFactory.create(code="CA")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_101,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            channel=NimbusExperiment.Channel.RELEASE,
            languages=[language_en],
            locales=[],
            countries=[country_ca],
            is_sticky=True,
        )

        sticky_expression = (
            "("
            "(is_already_enrolled) "
            "|| "
            "("
            "(days_since_install < 7) "
            "&& (app_version|versionCompare('100.!') >= 0) "
            "&& (language in ['en']) "
            "&& (region in ['CA'])"
            ")"
            ")"
        )
        self.assertEqual(
            experiment.targeting,
            f"(app_version|versionCompare('101.*') <= 0) && {sticky_expression}",
        )
        JEXLParser().parse(experiment.targeting)

    def test_targeting_with_sticky_and_no_advanced_targeting_omits_sticky_expression(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.RELEASE,
            languages=[],
            locales=[],
            countries=[],
            is_sticky=True,
        )

        self.assertEqual(
            experiment.targeting,
            '(browserSettings.update.channel == "release")',
        )
        JEXLParser().parse(experiment.targeting)

    @mock_valid_features
    def test_targeting_with_prevent_pref_conflicts_set_prefs(self):
        Features.clear_cache()
        call_command("load_feature_configs")

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.RELEASE,
            languages=[],
            locales=[],
            countries=[],
            prevent_pref_conflicts=True,
            feature_configs=[
                NimbusFeatureConfig.objects.get(
                    application=NimbusExperiment.Application.DESKTOP,
                    slug="oldSetPrefFeature",
                )
            ],
        )

        self.assertEqual(
            experiment.targeting,
            (
                '(browserSettings.update.channel == "release") && '
                "((experiment.slug in activeExperiments) || ("
                "(!('nimbus.test.string'|preferenceIsUserSet)) && "
                "(!('nimbus.test.int'|preferenceIsUserSet)) && "
                "(!('nimbus.test.boolean'|preferenceIsUserSet))))"
            ),
        )
        JEXLParser().parse(experiment.targeting)

    @mock_valid_features
    def test_targeting_without_prevent_pref_conflicts_sets_prefs(self):
        Features.clear_cache()
        call_command("load_feature_configs")

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.RELEASE,
            languages=[],
            locales=[],
            countries=[],
            prevent_pref_conflicts=False,
            feature_configs=[
                NimbusFeatureConfig.objects.get(
                    application=NimbusExperiment.Application.DESKTOP,
                    slug="oldSetPrefFeature",
                )
            ],
        )

        self.assertEqual(
            experiment.targeting,
            ('(browserSettings.update.channel == "release")'),
        )
        JEXLParser().parse(experiment.targeting)

    @parameterized.expand(
        [
            (application, require, exclude, expected_targeting)
            for (application, (require, exclude, expected_targeting)) in [
                *product(
                    list(NimbusExperiment.Application),
                    [
                        ([], [], "true"),
                        ([("foo", None)], [], "('foo' in enrollments)"),
                        ([], [("bar", None)], "(('bar' in enrollments) == false)"),
                        (
                            [("foo", None), ("bar", None)],
                            [("baz", None)],
                            (
                                "(('baz' in enrollments) == false) && "
                                "('foo' in enrollments) && "
                                "('bar' in enrollments)"
                            ),
                        ),
                    ],
                ),
                *[
                    (
                        NimbusExperiment.Application.DESKTOP,
                        (
                            [("foo", "control")],
                            [],
                            "(enrollmentsMap['foo'] == 'control')",
                        ),
                    ),
                    (
                        NimbusExperiment.Application.DESKTOP,
                        (
                            [],
                            [("foo", "control")],
                            "((enrollmentsMap['foo'] == 'control') == false)",
                        ),
                    ),
                ],
                *product(
                    [
                        app
                        for app in NimbusExperiment.Application
                        if app != NimbusExperiment.Application.DESKTOP
                    ],
                    [
                        (
                            [("foo", "control")],
                            [],
                            "(enrollments_map['foo'] == 'control')",
                        ),
                        (
                            [],
                            [("foo", "control")],
                            "((enrollments_map['foo'] == 'control') == false)",
                        ),
                    ],
                ),
            ]
        ]
    )
    def test_targeting_excluded_required_experiments_branches(
        self, application, require, exclude, expected_targeting
    ):
        experiments = {
            slug: NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.CREATED,
                application=application,
                slug=slug,
                firefox_min_version=NimbusExperiment.Version.NO_VERSION,
                targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            )
            for slug in ("foo", "bar", "baz")
        }

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            slug="slug",
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )
        for required_slug, required_branch_slug in require:
            NimbusExperimentBranchThroughRequired.objects.create(
                parent_experiment=experiment,
                child_experiment=experiments[required_slug],
                branch_slug=required_branch_slug,
            )
        for excluded_slug, excluded_branch_slug in exclude:
            NimbusExperimentBranchThroughExcluded.objects.create(
                parent_experiment=experiment,
                child_experiment=experiments[excluded_slug],
                branch_slug=excluded_branch_slug,
            )

        self.assertEqual(experiment.targeting, expected_targeting)
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

    def test_proposed_release_date_returns_None_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.proposed_release_date)

    def test_end_date_returns_None_for_not_ended_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        self.assertIsNone(experiment.end_date)

    def test_launch_month_returns_release_date_month_for_started_first_run_experiment(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            proposed_release_date=datetime.date.today() + datetime.timedelta(days=1),
            is_first_run=True,
        )

        self.assertIsNotNone(experiment.proposed_release_date)
        self.assertEqual(
            experiment.launch_month, experiment.proposed_release_date.strftime("%B")
        )

    @parameterized.expand([[True, datetime.date.today()], [False, None]])
    def test_release_date_for_first_run_experiment(self, first_run, expected_value):
        release_date = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            proposed_release_date=release_date,
            is_first_run=first_run,
        )

        self.assertEqual(experiment.release_date, expected_value)
        self.assertEqual(experiment.proposed_release_date, release_date)

    def test_launch_month_returns_enrollment_start_date(self):
        release_date = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            proposed_release_date=release_date,
            is_first_run=True,
        )

        self.assertEqual(experiment.release_date, release_date)
        self.assertEqual(experiment.launch_month, experiment.release_date.strftime("%B"))

    @parameterized.expand(
        [[NimbusExperiment.Status.LIVE], [NimbusExperiment.Status.COMPLETE]]
    )
    def test_start_date_uses_most_recent_start_change_without_cache(self, status):
        experiment = NimbusExperimentFactory.create(status=status)
        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.datetime.now() + datetime.timedelta(days=1),
        )
        start_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.datetime.now() + datetime.timedelta(days=2),
        )
        self.assertEqual(experiment.start_date, start_change.changed_on.date())

    @parameterized.expand(
        [[NimbusExperiment.Status.LIVE], [NimbusExperiment.Status.COMPLETE]]
    )
    def test_start_date_uses_cached_start_date(self, status):
        cached_date = datetime.date(2022, 1, 1)
        changelog_date = datetime.date(2022, 1, 2)

        experiment = NimbusExperimentFactory.create(status=status)
        experiment._start_date = cached_date
        experiment.save()

        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=changelog_date,
        )

        self.assertEqual(experiment.start_date, cached_date)

    def test_end_date_uses_most_recent_end_change_without_cache(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.COMPLETE
        )
        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=datetime.datetime.now() + datetime.timedelta(days=1),
        )
        end_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=datetime.datetime.now() + datetime.timedelta(days=2),
        )
        self.assertEqual(experiment.end_date, end_change.changed_on.date())

    def test_end_date_uses_cached_end_date(self):
        cached_date = datetime.date(2022, 1, 1)
        changelog_date = datetime.date(2022, 1, 2)

        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.COMPLETE
        )
        experiment._end_date = cached_date
        experiment.save()

        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=changelog_date,
        )

        self.assertEqual(experiment.end_date, cached_date)

    def test_enrollment_duration_for_ended_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_first_run=True,
            proposed_release_date=datetime.date.today() + datetime.timedelta(days=1),
        )

        expected_enrollment_duration = "{start} to {end}".format(
            start=experiment.proposed_release_date.strftime("%Y-%m-%d"),
            end=experiment.computed_end_date.strftime("%Y-%m-%d"),
        )
        self.assertEqual(experiment.enrollment_duration, expected_enrollment_duration)

    def test_enrollment_duration_for_not_started_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        self.assertEqual(experiment.enrollment_duration, experiment.proposed_duration)

    def test_end_date_uses_most_recent_end_change(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.COMPLETE
        )
        NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=datetime.datetime.now() + datetime.timedelta(days=1),
        )
        end_change = NimbusChangeLogFactory(
            experiment=experiment,
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
            changed_on=datetime.datetime.now() + datetime.timedelta(days=2),
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
            is_first_run=True,
            proposed_release_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
        )
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

    def test_first_run_end_enrollment_returns_True_after_proposed_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_first_run=True,
            proposed_release_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_enrollment=10,
        )
        self.assertTrue(experiment.should_end_enrollment)

    def test_end_enrollment_returns_True_after_proposed_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_enrollment=10,
        )
        self.assertTrue(experiment.should_end_enrollment)

    def test_computed_enrollment_days_returns_changed_on_minus_start_date(self):
        expected_days = 3
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=expected_days),
        )

        experiment.changes.filter(experiment_data__is_paused=True).update(
            changed_on=datetime.datetime.now()
        )

        self.assertEqual(
            experiment.computed_enrollment_days,
            expected_days,
        )

    def test_computed_enrollment_days_uses_end_date_without_pause_with_start_date(self):
        expected_days = 5
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE_WITHOUT_PAUSE,
            proposed_enrollment=99,
            start_date=datetime.date.today() - datetime.timedelta(days=expected_days),
            end_date=datetime.date.today(),
        )

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
        self,
        lifecycle,
    ):
        expected_days = 99
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            # Setting the span shouldn't apply while pending approval
            is_first_run=True,
            proposed_release_date=datetime.date.today() - datetime.timedelta(days=5),
            proposed_enrollment=expected_days,
        )

        experiment.changes.filter(experiment_data__is_paused=True).update(
            changed_on=datetime.datetime.now()
        )
        self.assertEqual(
            experiment.computed_enrollment_days,
            expected_days,
        )

    def test_computed_enrollment_days_returns_duration_if_is_paused_missing(self):
        expected_days = 99
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
            proposed_enrollment=expected_days,
        )
        experiment.changes.filter(experiment_data__is_paused=True).update(
            experiment_data={}
        )
        self.assertEqual(
            experiment.computed_enrollment_days,
            expected_days,
        )

    def test_computed_enrollment_days_returns_duration_if_experiment_data_is_none(self):
        expected_days = 99
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
            proposed_enrollment=expected_days,
        )
        experiment.changes.filter(experiment_data__is_paused=True).update(
            experiment_data=None
        )
        self.assertEqual(
            experiment.computed_enrollment_days,
            expected_days,
        )

    def test_computed_enrollment_end_date_returns_start_date_plus_enrollment_days(
        self,
    ):
        start_date = datetime.date(2022, 1, 1)
        enrollment_end_date = start_date + datetime.timedelta(days=7)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_APPROVE,
            start_date=start_date,
            proposed_release_date=None,
            proposed_enrollment=7,
        )

        experiment.changes.filter(experiment_data__is_paused=True).update(
            changed_on=enrollment_end_date
        )

        self.assertEqual(
            experiment.computed_enrollment_end_date,
            enrollment_end_date,
        )

    def test_computed_enrollment_end_date_returns_fallback(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        self.assertIsNone(experiment.computed_enrollment_end_date)

    def test_actual_enrollment_end_date_returns_none_before_enrollment_end(self):
        start_date = datetime.date(2022, 1, 1)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            start_date=start_date,
            proposed_enrollment=2,
        )

        self.assertIsNone(experiment.actual_enrollment_end_date)

    def test_actual_enrollment_end_date_returns_date_after_enrollment_end(self):
        start_date = datetime.date(2022, 1, 1)
        enrollment_end_date = datetime.date(2022, 1, 5)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
            start_date=start_date,
            proposed_enrollment=2,
            _enrollment_end_date=enrollment_end_date,
        )

        self.assertEqual(experiment.actual_enrollment_end_date, enrollment_end_date)

    def test_computed_duration_days_returns_end_date_minus_start_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            proposed_duration=10,
            start_date=datetime.date.today() - datetime.timedelta(days=7),
            proposed_release_date=None,
            end_date=datetime.date.today(),
        )

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

    def test_monitoring_dashboard_url_is_valid_when_experiment_not_begun(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=NimbusExperiment.Status.DRAFT,
            is_rollout=False,
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

    @parameterized.expand(
        [
            NimbusExperiment.Status.DRAFT,
            NimbusExperiment.Status.COMPLETE,
            NimbusExperiment.Status.LIVE,
            NimbusExperiment.Status.PREVIEW,
        ]
    )
    def test_monitoring_dashboard_returns_url_when_rollout(self, status):
        experiment = NimbusExperimentFactory.create(
            slug="experiment",
            status=status,
            is_rollout=True,
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="experiment",
            start_date=datetime.date(2019, 5, 1),
            status=NimbusExperiment.Status.LIVE,
            is_rollout=False,
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date(2019, 5, 1),
            end_date=datetime.date(2019, 5, 10),
            slug="experiment",
            status=NimbusExperiment.Status.COMPLETE,
            is_rollout=False,
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

    def test_rollouts_monitoring_dashboard_returns_correct_formatted_url(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            slug="rollout-1-slug",
            is_rollout=True,
            status=NimbusExperiment.Status.LIVE,
        )

        expected_slug = "rollout_1_slug"
        url = experiment.rollout_monitoring_dashboard_url
        assert url
        actual_slug = url[(url.index("::") + 2) :]  # take a slice of the url after '::'
        self.assertEqual(expected_slug, actual_slug)

        self.assertEqual(
            experiment.rollout_monitoring_dashboard_url,
            settings.ROLLOUT_MONITORING_URL.format(
                slug=expected_slug,
            ),
        )

    @parameterized.expand(
        [
            (False, NimbusExperimentFactory.Lifecycles.CREATED),
            (True, NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE),
            (True, NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING),
            (True, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.PREVIEW),
        ]
    )
    def test_rollouts_monitoring_dashboard_returns_url(self, valid_status, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=lifecycle,
            slug="rollout-1-slug",
            is_rollout=True,
        )

        if valid_status:
            expected_slug = "rollout_1_slug"
            self.assertEqual(
                experiment.rollout_monitoring_dashboard_url,
                settings.ROLLOUT_MONITORING_URL.format(
                    slug=expected_slug,
                ),
            )
        else:
            self.assertIsNone(experiment.rollout_monitoring_dashboard_url)

    def test_rollouts_monitoring_dashboard_returns_none_when_not_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            slug="rollout-1-slug",
            is_rollout=False,
            status=NimbusExperiment.Status.COMPLETE,
        )
        self.assertIsNone(experiment.rollout_monitoring_dashboard_url)

    def test_review_url_should_return_simple_review_url(self):
        with override_settings(
            KINTO_ADMIN_URL="https://remote-settings.allizom.org/v1/admin/",
        ):
            expected = (
                "https://remote-settings.allizom.org/v1/admin/#/buckets/main-workspace"
                "/collections/nimbus-desktop-experiments/simple-review"
            )
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
                application=NimbusExperiment.Application.DESKTOP,
            )
            self.assertEqual(experiment.review_url, expected)

    def test_review_url_stage_should_return_simple_review_url_without_slash(self):
        with override_settings(
            KINTO_ADMIN_URL="http://localhost:8888/v1/admin",
        ):
            expected = (
                "http://localhost:8888/v1/admin#/buckets/main-workspace"
                "/collections/nimbus-desktop-experiments/simple-review"
            )
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
            is_rollout=False,
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
            NimbusExperimentFactory.Lifecycles.CREATED,
            population_percent=Decimal("50.0"),
        )
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 5000)

        experiment.population_percent = Decimal("20.0")
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 2000)

    def test_allocate_buckets_for_live_approved_rollout(self):
        feature = NimbusFeatureConfigFactory(slug="feature")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE,
            population_percent=Decimal("50.0"),
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
            is_rollout=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
        )
        experiment.allocate_bucket_range()
        self.assertEqual(experiment.bucket_range.count, 5000)
        self.assertEqual(
            experiment.bucket_range.isolation_group.name,
            "firefox-desktop-feature-release-mac_only-rollout",
        )

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
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            population_percent=Decimal("50.0"),
        )
        original_namespace = experiment.bucket_namespace

        experiment.is_rollout = True
        experiment.save()

        self.assertNotEqual(original_namespace, experiment.bucket_namespace)
        self.assertEqual(
            experiment.bucket_namespace,
            "firefox-desktop-feature-release-mac_only-rollout",
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

    def test_first_run_proposed_enrollment_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_first_run=True,
            start_date=datetime.date.today(),
            proposed_release_date=datetime.date.today() + datetime.timedelta(days=10),
            proposed_enrollment=10,
            with_latest_change_now=True,
        )
        self.assertEqual(
            experiment.proposed_enrollment_end_date,
            datetime.date.today() + datetime.timedelta(days=20),
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date(2019, 5, 1),
        )

        self.assertTrue(experiment.results_ready)

    def test_results_ready_false(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=2),
        )

        self.assertFalse(experiment.results_ready)

    @parameterized.expand(
        [
            ({"v2": {"overall": {"enrollments": {"all": {}}}}},),
            ({"v2": {"weekly": {"enrollments": {"all": {}}}}},),
        ]
    )
    def test_has_displayable_results_true(self, results_data):
        experiment = NimbusExperimentFactory.create()
        experiment.results_data = results_data
        experiment.save()

        self.assertTrue(experiment.has_displayable_results)

    @parameterized.expand(
        [
            ({},),
            ({"v2": {}},),
            ({"v2": {"overall": {}}},),
            ({"v2": {"weekly": {}}},),
            ({"v2": {"overall": {"enrollments": {}}}},),
            ({"v2": {"weekly": {"enrollments": {}}}},),
            ({"v2": {"overall": {"enrollments": {"all": None}}}},),
            ({"v2": {"weekly": {"enrollments": {"all": None}}}},),
        ]
    )
    def test_has_displayable_results_false(self, results_data):
        experiment = NimbusExperimentFactory.create()
        experiment.results_data = results_data
        experiment.save()

        self.assertFalse(experiment.has_displayable_results)

    def test_show_results_url_true(self):
        lifecycle = NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, start_date=datetime.date(2020, 1, 1), proposed_enrollment=2
        )
        experiment.results_data = {"v2": {"overall": {"enrollments": {"all": {}}}}}
        experiment.is_rollout = False
        experiment.save()

        self.assertTrue(experiment.show_results_url)

    @parameterized.expand(
        [
            ({}, datetime.date(2020, 1, 1), False),
            (
                {"v2": {"overall": {"enrollments": {"all": {}}}}},
                datetime.date.today(),
                False,
            ),
            (
                {"v2": {"overall": {"enrollments": {"all": {}}}}},
                datetime.date(2020, 1, 1),
                True,
            ),
        ]
    )
    def test_show_results_url_false(self, results_data, start_date, is_rollout):
        lifecycle = NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, start_date=start_date, proposed_enrollment=2
        )
        experiment.results_data = results_data
        experiment.is_rollout = is_rollout
        experiment.save()

        self.assertFalse(experiment.show_results_url)

    @parameterized.expand(
        [
            (
                NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
                datetime.date(2020, 1, 1),
                None,
                False,
            ),
            (
                NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
                datetime.date.today(),
                None,
                False,
            ),
            (
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
                datetime.date(2020, 1, 1),
                datetime.date(2020, 2, 3),
                True,
            ),
        ]
    )
    def test_results_expected_date(
        self, lifecycle, start_date, end_date, is_paused_published
    ):
        proposed_enrollment = 2
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=lifecycle,
            start_date=start_date,
            end_date=end_date,
            proposed_enrollment=proposed_enrollment,
        )

        expected_date = (
            start_date
            + datetime.timedelta(days=proposed_enrollment)
            + datetime.timedelta(days=NimbusConstants.DAYS_UNTIL_ANALYSIS)
        )
        self.assertEqual(experiment.results_expected_date, expected_date)

    def test_results_expected_date_null(self):
        lifecycle = NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, start_date=datetime.date(2020, 1, 1), proposed_enrollment=2
        )
        experiment.is_rollout = True
        experiment.save()

        self.assertIsNone(experiment.results_expected_date)

    @parameterized.expand(
        [
            (True, NimbusExperimentFactory.Lifecycles.CREATED),
            (True, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_REJECT),
            (True, NimbusExperimentFactory.Lifecycles.LAUNCH_REJECT),
            (False, NimbusExperimentFactory.Lifecycles.PREVIEW),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_DIRTY),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_REJECT),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_TIMEOUT),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_REJECT),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_REJECT_MANUAL_ROLLBACK),
            (False, NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_WAITING),
            (False, NimbusExperimentFactory.Lifecycles.LIVE_REVIEW_REQUESTED),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED),
        ]
    )
    def test_experiment_can_edit(self, expected_can_edit, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, is_rollout=False
        )
        self.assertEqual(experiment.can_edit, expected_can_edit)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_REJECT,),
            (NimbusExperimentFactory.Lifecycles.LAUNCH_REJECT,),
            (NimbusExperimentFactory.Lifecycles.LIVE_DIRTY,),
            (NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_REJECT,),
            (NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_TIMEOUT,),
            (NimbusExperimentFactory.Lifecycles.LIVE_REJECT,),
            (NimbusExperimentFactory.Lifecycles.LIVE_REJECT_MANUAL_ROLLBACK,),
            (NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_REJECT,),
            (NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_APPROVE_REJECT,),
        ]
    )
    def test_rollout_can_edit(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, is_rollout=True
        )
        self.assertTrue(experiment.can_edit)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_APPROVE_TIMEOUT,),
            (NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_APPROVE_WAITING,),
            (
                NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_REJECT_MANUAL_ROLLBACK,
            ),
            (NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_APPROVE_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,),
            (NimbusExperimentFactory.Lifecycles.LIVE_APPROVE,),
            (NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_WAITING,),
            (NimbusExperimentFactory.Lifecycles.LIVE_REVIEW_REQUESTED,),
            (NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED,),
        ]
    )
    def test_rollout_cannot_edit(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, is_rollout=True
        )
        self.assertFalse(experiment.can_edit)

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
        required_experiment = NimbusExperimentFactory.create()
        excluded_experiment = NimbusExperimentFactory.create()
        parent = NimbusExperiment.objects.create(
            owner=owner,
            name="Parent Experiment",
            slug="parent-experiment",
            application=NimbusExperiment.Application.DESKTOP,
            conclusion_recommendation="RERUN",
            takeaways_summary="takeaway",
        )
        NimbusExperimentBranchThroughRequired.objects.create(
            parent_experiment=parent,
            child_experiment=required_experiment,
            branch_slug=required_experiment.reference_branch.slug,
        )
        NimbusExperimentBranchThroughExcluded.objects.create(
            parent_experiment=parent,
            child_experiment=excluded_experiment,
            branch_slug=excluded_experiment.reference_branch.slug,
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

        self.assertFalse(child.risk_partner_related)
        self.assertFalse(child.risk_revenue)
        self.assertFalse(child.risk_brand)
        self.assertFalse(NimbusBucketRange.objects.filter(experiment=child).exists())
        self.assertFalse(child.is_rollout_dirty)
        self.assertFalse(child.takeaways_metric_gain)
        self.assertFalse(child.takeaways_qbr_learning)
        self.assertEqual(child.locales.all().count(), 0)
        self.assertEqual(child.countries.all().count(), 0)
        self.assertEqual(child.languages.all().count(), 0)
        self.assertEqual(child.projects.all().count(), 0)
        self.assertEqual(child.branches.all().count(), 0)
        self.assertEqual(child.subscribers.all().count(), 0)
        self.assertEqual(child.changes.all().count(), 1)
        self.assertIsNone(child.conclusion_recommendation)
        self.assertIsNone(child.takeaways_gain_amount)
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
        parent.is_rollout = True
        self._clone_experiment_and_assert_common_expectations(parent, rollout_branch.slug)

    def test_clone_with_rollout_branch_slug_invalid(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        parent.is_rollout = True
        with self.assertRaises(NimbusBranch.DoesNotExist):
            self._clone_experiment_and_assert_common_expectations(parent, "BAD SLUG")

    def test_clone_dirty_rollout(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY,
            is_rollout=True,
            is_rollout_dirty=True,
        )
        rollout_branch = parent.branches.first()
        child = self._clone_experiment_and_assert_common_expectations(
            parent,
            rollout_branch.slug,
        )
        self.assertFalse(child.is_rollout_dirty)

    def _clone_experiment_and_assert_common_expectations(
        self, parent, rollout_branch_slug=None
    ):
        child = parent.clone("Child Experiment", parent.owner, rollout_branch_slug)

        # Explicitly set fields
        self.assertEqual(child.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(child.status_next, None)
        self.assertEqual(child.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(child.owner, parent.owner)
        self.assertEqual(child.parent, parent)
        self.assertEqual(child.is_archived, False)
        self.assertEqual(child.is_paused, False)
        self.assertEqual(child.is_rollout_dirty, False)
        self.assertEqual(child.proposed_release_date, None)
        self.assertEqual(child.release_date, None)
        self.assertEqual(child.enrollment_start_date, None)
        self.assertEqual(child.published_dto, None)
        self.assertEqual(child.results_data, None)
        self.assertEqual(child.takeaways_gain_amount, None)
        self.assertEqual(child.takeaways_metric_gain, False)
        self.assertEqual(child.takeaways_qbr_learning, False)
        self.assertEqual(child.takeaways_summary, None)
        self.assertEqual(child.conclusion_recommendation, None)
        self.assertEqual(child.qa_status, NimbusExperiment.QAStatus.NOT_SET)
        self.assertEqual(child.qa_comment, None)
        self.assertEqual(child._start_date, None)
        self.assertEqual(child._end_date, None)
        self.assertEqual(child._enrollment_end_date, None)

        # Cloned fields
        self.assertEqual(child.name, "Child Experiment")
        self.assertEqual(child.slug, "child-experiment")
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

        self.assertEqual(
            set(child.languages.all().values_list("code", flat=True)),
            set(parent.languages.all().values_list("code", flat=True)),
        )
        self.assertEqual(
            set(child.projects.all().values_list("slug", flat=True)),
            set(parent.projects.all().values_list("slug", flat=True)),
        )
        self.assertEqual(
            set(child.subscribers.all().values_list("id", flat=True)),
            set(),
        )

        self.assertEqual(child.is_rollout, parent.is_rollout)

        self.assertEqual(
            {
                (eb.child_experiment.slug, eb.branch_slug)
                for eb in NimbusExperimentBranchThroughRequired.objects.filter(
                    parent_experiment=parent
                )
            },
            {
                (eb.child_experiment.slug, eb.branch_slug)
                for eb in NimbusExperimentBranchThroughRequired.objects.filter(
                    parent_experiment=child
                )
            },
        )
        self.assertEqual(
            {
                (eb.child_experiment.slug, eb.branch_slug)
                for eb in NimbusExperimentBranchThroughExcluded.objects.filter(
                    parent_experiment=parent
                )
            },
            {
                (eb.child_experiment.slug, eb.branch_slug)
                for eb in NimbusExperimentBranchThroughExcluded.objects.filter(
                    parent_experiment=child
                )
            },
        )

        for parent_link in parent.documentation_links.all():
            child_link = child.documentation_links.get(title=parent_link.title)
            self.assertEqual(child_link.link, parent_link.link)

        self.assertEqual(child.changes.all().count(), 1)

        if rollout_branch_slug:
            self.assertTrue(child.is_rollout)
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
            self.assertFalse(child.is_rollout)
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

    def test_get_changelogs_without_prior_change(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        current_datetime = datetime.datetime(2021, 1, 1).date()
        timestamp = timezone.make_aware(
            datetime.datetime.combine(current_datetime, datetime.datetime.min.time())
        )
        time_format = "%I:%M %p %Z"
        local_timestamp = timezone.localtime(timestamp)
        formatted_timestamp = local_timestamp.strftime(time_format)

        experiment_changelogs = experiment.get_changelogs_by_date()

        self.assertEqual(len(experiment_changelogs[0]["changes"]), 1)
        self.assertEqual(
            experiment_changelogs,
            [
                {
                    "date": current_datetime,
                    "changes": [
                        {
                            "event": ChangeEventType.CREATION.name,
                            "event_message": (
                                f"{experiment.owner} created this experiment"
                            ),
                            "changed_by": experiment.owner,
                            "timestamp": formatted_timestamp,
                        },
                    ],
                }
            ],
        )

    def test_initial_log_of_cloned_experiment(self):
        experiment = NimbusExperimentFactory.create(
            slug="test-experiment",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        current_date = timezone.now().date()
        timestamp = timezone.make_aware(
            datetime.datetime.combine(current_date, datetime.datetime.min.time())
        )
        time_format = "%I:%M %p %Z"
        local_timestamp = timezone.localtime(timestamp)
        formatted_timestamp = local_timestamp.strftime(time_format)

        cloned_experiment = experiment.clone(
            "test experiment clone", user, changed_on=timestamp
        )

        experiment_changelogs = cloned_experiment.get_changelogs_by_date()

        self.assertEqual(len(experiment_changelogs[0]["changes"]), 1)
        self.assertEqual(
            experiment_changelogs,
            [
                {
                    "date": current_date,
                    "changes": [
                        {
                            "event": ChangeEventType.CREATION.name,
                            "event_message": (
                                f"{user} cloned this experiment from "
                                f"{cloned_experiment.parent.name}"
                            ),
                            "changed_by": user,
                            "timestamp": formatted_timestamp,
                        },
                    ],
                }
            ],
        )

    def test_get_changelogs(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        time_format = "%I:%M %p %Z"
        current_date = timezone.now().date()

        timestamp_1 = timezone.make_aware(
            datetime.datetime.combine(current_date, datetime.datetime.min.time())
        )
        local_timestamp_1 = timezone.localtime(timestamp_1)
        formatted_timestamp_1 = local_timestamp_1.strftime(time_format)

        timestamp_2 = timestamp_1 + timezone.timedelta(hours=2)
        local_timestamp_2 = timezone.localtime(timestamp_2)
        formatted_timestamp_2 = local_timestamp_2.strftime(time_format)

        timestamp_3 = timestamp_2 + timezone.timedelta(hours=2)
        local_timestamp_3 = timezone.localtime(timestamp_3)
        formatted_timestamp_3 = local_timestamp_3.strftime(time_format)

        generate_nimbus_changelog(experiment, user, "created", timestamp_1)

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, user, "publish_status change", timestamp_2)

        experiment.status = NimbusExperiment.Status.PREVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, user, "status_next change", timestamp_3)

        experiment_changelogs = experiment.get_changelogs_by_date()

        self.assertEqual(len(experiment_changelogs[0]["changes"]), 3)

        self.assertEqual(
            experiment_changelogs,
            [
                {
                    "date": current_date,
                    "changes": [
                        {
                            "event": ChangeEventType.STATE.name,
                            "event_message": (
                                f"{user} changed value of Status from "
                                f"Draft to Preview"
                            ),
                            "changed_by": user,
                            "timestamp": formatted_timestamp_3,
                            "old_value": "Draft",
                            "new_value": "Preview",
                        },
                        {
                            "event": ChangeEventType.STATE.name,
                            "event_message": (
                                f"{user} changed value of Publish Status from "
                                f"Idle to Review"
                            ),
                            "changed_by": user,
                            "timestamp": formatted_timestamp_2,
                            "old_value": "Idle",
                            "new_value": "Review",
                        },
                        {
                            "event": ChangeEventType.CREATION.name,
                            "event_message": f"{user} created this experiment",
                            "changed_by": user,
                            "timestamp": formatted_timestamp_1,
                        },
                    ],
                }
            ],
        )

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Application.FENIX, 3),
            (NimbusExperiment.Application.FENIX, NimbusExperiment.Application.DESKTOP, 0),
        ]
    )
    def test_get_live_multifeature_experiments_for_feature(
        self,
        application1,
        application2,
        expected_matches,
    ):
        feature1 = NimbusFeatureConfigFactory.create()
        feature2 = NimbusFeatureConfigFactory.create()

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=application1,
            feature_configs=[feature1, feature2],
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=application1,
            feature_configs=[feature1, feature2],
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=application1,
            feature_configs=[feature1, feature2],
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application1,
            feature_configs=[feature1, feature2],
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application2,
            feature_configs=[feature1],
        )

        experiments = experiment.feature_has_live_multifeature_experiments
        self.assertEqual(len(experiments), expected_matches)

    def test_get_live_multifeature_experiments_for_feature_no_live(self):
        feature1 = NimbusFeatureConfigFactory.create()
        feature2 = NimbusFeatureConfigFactory.create()

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            feature_configs=[feature1, feature2],
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            feature_configs=[feature1, feature2],
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            feature_configs=[feature1, feature2],
        )

        experiments = experiment.feature_has_live_multifeature_experiments
        self.assertEqual(len(experiments), 0)

    def test_get_live_multifeature_experiments_for_feature_no_live_multifeature(self):
        feature1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature1],
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature1, feature2],
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature1],
        )

        experiments = experiment.feature_has_live_multifeature_experiments
        self.assertEqual(len(experiments), 0)

    def test_get_live_multifeature_experiments_none(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
        )

        experiments = experiment.feature_has_live_multifeature_experiments
        self.assertEqual(len(experiments), 0)

    def test_get_live_excluded_experiments(self):
        experiments = {
            slug: NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
                application=NimbusExperiment.Application.DESKTOP,
                targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            )
            for slug in ("foo", "bar", "baz")
        }
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            slug="slug",
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )

        for excluded_slug, excluded_branch_slug in [("foo", "control")]:
            NimbusExperimentBranchThroughExcluded.objects.create(
                parent_experiment=experiment,
                child_experiment=experiments[excluded_slug],
                branch_slug=excluded_branch_slug,
            )

        excluded_live_experiments = experiment.excluded_live_deliveries
        self.assertEqual(len(excluded_live_experiments), 1)
        self.assertEqual(excluded_live_experiments.first(), experiments["foo"].slug)

    def test_get_no_live_excluded_experiments(self):
        for slug in ("foo", "bar", "baz"):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
                slug=slug,
                application=NimbusExperiment.Application.DESKTOP,
                targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            slug="slug",
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )

        excluded_live_experiments = experiment.excluded_live_deliveries
        self.assertEqual(len(excluded_live_experiments), 0)
        self.assertEqual(excluded_live_experiments, [])

    def test_get_live_experiments_in_previous_namespaces(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiments = {
            slug: NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
                application=NimbusExperiment.Application.DESKTOP,
                channel=NimbusExperiment.Channel.RELEASE,
                firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
                firefox_max_version=NimbusExperiment.Version.FIREFOX_130,
                targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
                feature_configs=[feature],
            )
            for slug in ("foo", "bar", "baz")
        }

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            slug="slug2",
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_130,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            feature_configs=[feature],
        )

        matching_experiments = experiment.live_experiments_in_namespace
        self.assertEqual(len(matching_experiments), 3)
        self.assertEqual(
            list(matching_experiments.values_list("slug", flat=True)),
            sorted(
                [
                    experiments["bar"].slug,
                    experiments["baz"].slug,
                    experiments["foo"].slug,
                ]
            ),
        )

    def test_get_live_experiments_do_not_exist_in_previous_namespaces(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )

        for slug in ("foo", "bar", "baz"):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.CREATED,
                slug=slug,
                application=NimbusExperiment.Application.DESKTOP,
                channel=NimbusExperiment.Channel.RELEASE,
                firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
                firefox_max_version=NimbusExperiment.Version.FIREFOX_130,
                targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
                feature_configs=[feature],
            )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            slug="slug2",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_130,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature],
        )

        matching_experiments = experiment.live_experiments_in_namespace
        self.assertEqual(len(matching_experiments), 0)

    def test_get_live_experiments_in_different_namespaces(self):
        feature1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )

        for slug in ("foo", "bar", "baz"):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
                slug=slug,
                application=NimbusExperiment.Application.DESKTOP,
                channel=NimbusExperiment.Channel.RELEASE,
                firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
                firefox_max_version=NimbusExperiment.Version.FIREFOX_130,
                targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
                feature_configs=[feature1],
            )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            slug="slug2",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_130,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature2],
        )

        matching_experiments = experiment.live_experiments_in_namespace
        self.assertEqual(len(matching_experiments), 0)

    def test_get_live_experiments_in_different_namespaces_excludes_self(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            slug="slug2",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_130,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[NimbusFeatureConfigFactory.create()],
        )

        matching_experiments = experiment.live_experiments_in_namespace
        self.assertEqual(len(matching_experiments), 0)


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

    def test_latest_review_request_returns_change_for_dirty_to_review(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY,
            is_rollout=True,
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

    def test_latest_rejection_returns_rejection_for_review_to_dirty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY,
            is_rollout=True,
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

    def test_update_live_is_not_considered_latest_rejection(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_WAITING,
            is_rollout=True,
            published_dto={"id": "cool-cat", "test": False},
        )

        experiment.status = NimbusExperiment.Status.LIVE
        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.published_dto = {"id": "cool-cat", "test": True}

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
        now = datetime.datetime.now()
        user = UserFactory.create()
        changelog = NimbusChangeLogFactory.create(
            changed_by=user,
            changed_on=now,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.PREVIEW,
            message=None,
        )
        self.assertEqual(str(changelog), f"Draft > Preview by {user.email} on {now}")


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
            expected_filename = str(
                Path(self.experiment.slug, f"{mock_uuid4.return_value}.png"),
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
            expected_filename = str(
                Path(self.experiment.slug, f"{mock_uuid4.return_value}.png"),
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
            expected_filename = str(
                Path(self.experiment.slug, f"{mock_uuid4.return_value}.png"),
            )
            self.screenshot.save()
            self.screenshot.delete()
            mock_delete.assert_called_with(expected_filename)


class NimbusFeatureConfigTests(TestCase):
    def test_schemas_between_versions(self):
        feature = NimbusFeatureConfigFactory.create()

        versions = {
            (v.major, v.minor, v.patch): v
            for v in NimbusFeatureVersion.objects.bulk_create(
                NimbusFeatureVersion(
                    major=major,
                    minor=minor,
                    patch=patch,
                )
                for major in range(1, 3)
                for minor in range(3)
                for patch in range(3)
            )
        }

        schemas = {
            schema.version: schema
            for schema in NimbusVersionedSchema.objects.bulk_create(
                NimbusVersionedSchema(
                    feature_config=feature,
                    version=versions[(major, minor, patch)],
                    sets_prefs=[],
                )
                for major in range(1, 3)
                for minor in range(3)
                for patch in range(3)
            )
        }

        results = feature.schemas_between_versions(
            packaging.version.Version("1.2"),
            packaging.version.Version("2.1.1"),
        )

        self.assertEqual(
            set(results),
            {
                schemas[versions[v]]
                for v in (
                    (1, 2, 0),
                    (1, 2, 1),
                    (1, 2, 2),
                    (2, 0, 0),
                    (2, 0, 1),
                    (2, 0, 2),
                    (2, 1, 0),
                )
            },
        )

    def test_get_versioned_schema_range_min_version_max_version_unsupported(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusConstants.Application.DESKTOP
        )
        version = NimbusFeatureVersion.objects.create(major=121, minor=0, patch=0)
        unversioned_schema = NimbusVersionedSchema.objects.get(
            feature_config=feature, version=None
        )
        NimbusVersionedSchemaFactory.create(feature_config=feature, version=version)

        schemas_in_range = feature.get_versioned_schema_range(
            packaging.version.Version("111.0.0"), packaging.version.Version("112.0.0")
        )
        self.assertEqual(
            schemas_in_range,
            NimbusFeatureConfig.VersionedSchemaRange(
                schemas=[unversioned_schema],
                unsupported_in_range=False,
                unsupported_versions=[],
            ),
        )

    @parameterized.expand(
        [
            None,
            packaging.version.Version("122.0.0"),
        ]
    )
    def test_get_versioned_schema_range_min_version_unsupported(self, max_version):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusConstants.Application.DESKTOP
        )
        version = NimbusFeatureVersion.objects.create(major=121, minor=0, patch=0)
        versioned_schema = NimbusVersionedSchemaFactory.create(
            feature_config=feature, version=version
        )

        info = feature.get_versioned_schema_range(
            packaging.version.Version("111.0.0"), max_version
        )
        self.assertEqual(
            info,
            NimbusFeatureConfig.VersionedSchemaRange(
                schemas=[versioned_schema],
                unsupported_in_range=False,
                unsupported_versions=[],
            ),
        )

    def test_get_versioned_schema_range_unsupported_app(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusConstants.Application.DEMO_APP
        )
        unversioned_schema = feature.schemas.get(version=None)
        info = feature.get_versioned_schema_range(
            packaging.version.Version("1.0.0"), None
        )

        self.assertEqual(
            info,
            NimbusFeatureConfig.VersionedSchemaRange(
                schemas=[unversioned_schema],
                unsupported_in_range=False,
                unsupported_versions=[],
            ),
        )

    def test_get_versioned_schema_range_unsupported_in_range(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusConstants.Application.DESKTOP
        )
        version = NimbusFeatureVersion.objects.create(major=123, minor=0, patch=0)
        NimbusVersionedSchemaFactory.create(feature_config=feature, version=version)
        schemas_in_range = feature.get_versioned_schema_range(
            packaging.version.Version("121.0.0"), packaging.version.Version("122.0.0")
        )

        self.assertEqual(
            schemas_in_range,
            NimbusFeatureConfig.VersionedSchemaRange(
                schemas=[],
                unsupported_in_range=True,
                unsupported_versions=[],
            ),
        )

    def test_get_versioned_schema_range_unsupported_versions(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusConstants.Application.DESKTOP
        )
        versions = {
            (v.major, v.minor, v.patch): v
            for v in NimbusFeatureVersion.objects.bulk_create(
                NimbusFeatureVersion(major=major, minor=minor, patch=0)
                for major in (121, 122, 123)
                for minor in (0, 1)
            )
        }
        # There needs to exist another feature for the same app with versioned
        # schemas so that we can infer the application supports those versions.
        feature_2 = NimbusFeatureConfigFactory.create(
            application=NimbusConstants.Application.DESKTOP
        )
        NimbusVersionedSchema.objects.bulk_create(
            NimbusVersionedSchemaFactory.build(
                feature_config=feature_2,
                version=version,
            )
            for version in versions.values()
        )

        schema = NimbusVersionedSchemaFactory.create(
            feature_config=feature, version=versions[(122, 1, 0)]
        )
        schemas_in_range = feature.get_versioned_schema_range(
            packaging.version.Version("121.0.0"), packaging.version.Version("124.0.0")
        )

        self.assertEqual(
            schemas_in_range,
            NimbusFeatureConfig.VersionedSchemaRange(
                schemas=[schema],
                unsupported_in_range=False,
                unsupported_versions=[
                    versions[v]
                    for v in (
                        (123, 1, 0),
                        (123, 0, 0),
                        (122, 0, 0),
                        (121, 1, 0),
                        (121, 0, 0),
                    )
                ],
            ),
        )

    def test_get_versioned_schema_range(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusConstants.Application.DESKTOP
        )
        versions = {
            (v.major, v.minor, v.patch): v
            for v in NimbusFeatureVersion.objects.bulk_create(
                NimbusFeatureVersion(major=major, minor=minor, patch=0)
                for major in (121, 122, 123)
                for minor in (0, 1)
            )
        }
        schemas = {
            schema.version: schema
            for schema in NimbusVersionedSchema.objects.bulk_create(
                NimbusVersionedSchemaFactory.build(
                    feature_config=feature,
                    version=version,
                )
                for version in versions.values()
            )
        }

        schemas_in_range = feature.get_versioned_schema_range(
            packaging.version.Version("122.0.0"), packaging.version.Version("123.1.0")
        )

        self.assertEqual(
            schemas_in_range,
            NimbusFeatureConfig.VersionedSchemaRange(
                schemas=[
                    schemas[versions[v]]
                    for v in (
                        (123, 0, 0),
                        (122, 1, 0),
                        (122, 0, 0),
                    )
                ],
                unsupported_in_range=False,
                unsupported_versions=[],
            ),
        )
