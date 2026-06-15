import datetime

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.models import (
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
)
from experimenter.experiments.tests.factories import (
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
)
from experimenter.nimbus_ui.new.forms import (
    RolloutAudienceForm,
    RolloutOverviewForm,
    RolloutQAStatusForm,
    RolloutRisksForm,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.targeting.constants import NimbusTargetingConfig


class RequestFormTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(email="dev@example.com")
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("nimbus-ui-create"))
        self.request.user = self.user


class TestRolloutOverviewForm(RequestFormTestCase):
    def test_valid_form_saves(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )

        form = RolloutOverviewForm(
            instance=experiment,
            data={
                "name": "new rollout name",
                "hypothesis": "new hypothesis",
                "public_description": "new description",
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.name, "new rollout name")
        self.assertEqual(experiment.hypothesis, "new hypothesis")
        self.assertEqual(experiment.public_description, "new description")

        documentation_link = experiment.documentation_links.all().get()
        self.assertEqual(
            documentation_link.title, NimbusExperiment.DocumentationLink.DESIGN_DOC
        )
        self.assertEqual(documentation_link.link, "https://www.example.com")
        self.assertEqual(
            form.get_changelog_message(),
            f"{self.request.user} updated rollouts overview",
        )

    def test_name_field_is_required(self):
        form_data = {
            "name": "",
            "hypothesis": "new hypothesis",
            "public_description": "new description",
            "documentation_links-TOTAL_FORMS": "0",
            "documentation_links-INITIAL_FORMS": "0",
        }

        form = RolloutOverviewForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class TestRolloutRisksForm(RequestFormTestCase):
    def test_valid_form_saves(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            risk_brand=False,
            risk_message=False,
            risk_revenue=False,
            risk_partner_related=False,
            risk_ai=False,
        )
        form = RolloutRisksForm(
            instance=experiment,
            data={
                "risk_brand": True,
                "risk_message": True,
                "risk_revenue": True,
                "risk_partner_related": True,
                "risk_ai": True,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertTrue(experiment.risk_brand)
        self.assertTrue(experiment.risk_message)
        self.assertTrue(experiment.risk_revenue)
        self.assertTrue(experiment.risk_partner_related)
        self.assertTrue(experiment.risk_ai)
        self.assertEqual(
            form.get_changelog_message(), f"{self.request.user} updated rollout risks"
        )


class TestRolloutAudienceForm(RequestFormTestCase):
    def _audience_data(self, **overrides):
        data = {
            "channel": NimbusExperiment.Channel.BETA,
            "channels": [NimbusExperiment.Channel.BETA],
            "countries": [],
            "exclude_countries": False,
            "exclude_languages": False,
            "exclude_locales": False,
            "excluded_experiments_branches": [],
            "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
            "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
            "is_first_run": False,
            "is_sticky": False,
            "languages": [],
            "locales": [],
            "localizations": "",
            "required_experiments_branches": [],
            "targeting_config_slug": NimbusExperiment.TargetingConfig.NO_TARGETING,
        }
        data.update(overrides)
        return data

    def test_valid_form_saves_desktop(self):
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            channels=[NimbusExperiment.Channel.NIGHTLY],
            countries=[],
            locales=[],
            languages=[],
        )

        form = RolloutAudienceForm(
            instance=experiment,
            data=self._audience_data(
                channels=[
                    NimbusExperiment.Channel.NIGHTLY,
                    NimbusExperiment.Channel.BETA,
                ],
                countries=[country.id],
                exclude_countries=True,
                exclude_languages=True,
                exclude_locales=True,
                excluded_experiments_branches=[f"{excluded.slug}:control"],
                is_first_run=True,
                is_sticky=True,
                languages=[language.id],
                locales=[locale.id],
                required_experiments_branches=[f"{required.slug}:None"],
                targeting_config_slug=NimbusExperiment.TargetingConfig.FIRST_RUN,
            ),
            request=self.request,
        )

        self.assertIn(
            form.format_branch_choice(excluded.slug, excluded.name, None),
            form.fields["excluded_experiments_branches"].choices,
        )
        self.assertIn(
            form.format_branch_choice(excluded.slug, excluded.name, "control"),
            form.fields["excluded_experiments_branches"].choices,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(
            set(experiment.channels),
            {NimbusExperiment.Channel.NIGHTLY, NimbusExperiment.Channel.BETA},
        )
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])
        self.assertEqual(list(experiment.languages.all()), [language])
        self.assertTrue(experiment.exclude_countries)
        self.assertTrue(experiment.exclude_locales)
        self.assertTrue(experiment.exclude_languages)
        self.assertTrue(experiment.is_first_run)
        self.assertTrue(experiment.is_sticky)
        self.assertTrue(
            NimbusExperimentBranchThroughExcluded.objects.filter(
                parent_experiment=experiment,
                child_experiment=excluded,
                branch_slug="control",
            ).exists()
        )
        self.assertTrue(
            NimbusExperimentBranchThroughRequired.objects.filter(
                parent_experiment=experiment,
                child_experiment=required,
                branch_slug=None,
            ).exists()
        )
        self.assertEqual(
            form.get_changelog_message(), f"{self.request.user} updated audience"
        )

    def test_check_rollout_dirty_does_not_set_flag_for_non_rollout(self):
        experiment = NimbusExperimentFactory.create(
            is_rollout=False,
            population_percent=5,
            application=NimbusExperiment.Application.DESKTOP,
            channels=[NimbusExperiment.Channel.BETA],
        )

        form = RolloutAudienceForm(
            instance=experiment,
            data=self._audience_data(population_percent=10),
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        updated_experiment = form.save()
        updated_experiment.refresh_from_db()

        self.assertFalse(updated_experiment.is_rollout_dirty)

    def test_targeting_config_choices_filtered_by_application_and_sorted(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        form = RolloutAudienceForm(instance=experiment, request=self.request)

        actual_choices = form.fields["targeting_config_slug"].choices
        application = NimbusExperiment.Application(experiment.application)
        expected_choices = sorted(
            [
                (targeting.slug, f"{targeting.name} - {targeting.description}")
                for targeting in NimbusTargetingConfig.targeting_configs
                if application.name in targeting.application_choice_names
            ],
            key=lambda choice: choice[1].lower(),
        )

        self.assertEqual(actual_choices, expected_choices)

    def test_initial_experiment_branch_choices_include_existing_relations(self):
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            required_experiments_branches=[required],
            excluded_experiments_branches=[excluded],
        )

        form = RolloutAudienceForm(instance=experiment, request=self.request)

        self.assertEqual(
            form.initial["required_experiments_branches"],
            [f"{required.slug}:{required.reference_branch.slug}"],
        )
        self.assertEqual(
            form.initial["excluded_experiments_branches"],
            [f"{excluded.slug}:{excluded.reference_branch.slug}"],
        )


class TestRolloutQAStatusForm(RequestFormTestCase):
    def test_form_updates_qa_fields_and_qa_run_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            qa_status=NimbusExperiment.QAStatus.NOT_SET,
            qa_run_date=None,
        )
        data = {
            "qa_status": NimbusExperiment.QAStatus.SELF_GREEN,
            "qa_comment": "QA completed",
            "qa_run_test_plan_url": "https://www.example.com/test-plan",
            "qa_run_testrail_url": "https://www.example.com/testrail",
        }
        form = RolloutQAStatusForm(data, request=self.request, instance=experiment)

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.qa_status, NimbusExperiment.QAStatus.SELF_GREEN)
        self.assertEqual(experiment.qa_run_date, timezone.now().date())
        self.assertEqual(experiment.qa_comment, "QA completed")
        self.assertEqual(
            experiment.qa_run_test_plan_url, "https://www.example.com/test-plan"
        )
        self.assertEqual(
            experiment.qa_run_testrail_url, "https://www.example.com/testrail"
        )
        self.assertEqual(form.get_changelog_message(), f"{self.request.user} updated QA")

    def test_form_does_not_update_qa_run_date_when_changing_to_not_set(self):
        old_date = datetime.date(2024, 1, 1)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            qa_status=NimbusExperiment.QAStatus.SELF_GREEN,
            qa_run_date=old_date,
        )
        data = {
            "qa_status": NimbusExperiment.QAStatus.NOT_SET,
            "qa_comment": "",
            "qa_run_test_plan_url": "",
            "qa_run_testrail_url": "",
        }
        form = RolloutQAStatusForm(data, request=self.request, instance=experiment)

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.qa_status, NimbusExperiment.QAStatus.NOT_SET)
        self.assertEqual(experiment.qa_run_date, old_date)


class TestSelectedFirstMixin(TestCase):
    def test_selected_options_appear_first(self):
        LocaleFactory.create(code="en-US", name="English (US)")
        LocaleFactory.create(code="de-DE", name="German (Germany)")
        locale1 = LocaleFactory.create(code="fr-FR", name="French (France)")
        locale2 = LocaleFactory.create(code="es-ES", name="Spanish (Spain)")

        experiment = NimbusExperimentFactory.create()
        experiment.locales.set([locale1, locale2])

        form = RolloutAudienceForm(instance=experiment)
        bound_field = form["locales"]

        first_two_ids = {
            int(str(bound_field[0].data["value"])),
            int(str(bound_field[1].data["value"])),
        }

        self.assertEqual(first_two_ids, {locale1.id, locale2.id})
