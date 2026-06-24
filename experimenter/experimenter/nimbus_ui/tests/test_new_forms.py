import datetime
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized

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
    TagFactory,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.nimbus_ui.new.forms import (
    CollaboratorsForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    DraftToLiveRolloutForm,
    DraftToPreviewRolloutForm,
    LiveToPausedRolloutForm,
    LiveToUpdateRolloutForm,
    NimbusExperimentCreateForm,
    NimbusExperimentSidebarCloneForm,
    PausedToLiveRolloutForm,
    PreviewToDraftRolloutForm,
    PreviewToLiveRolloutForm,
    RolloutAudienceForm,
    RolloutOverviewForm,
    RolloutQAStatusForm,
    RolloutRisksForm,
    TagAssignForm,
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


class TestNimbusExperimentCreateForm(RequestFormTestCase):
    def test_valid_form_creates_experiment_with_changelog(self):
        data = {
            "owner": self.user,
            "name": "Test Experiment",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.name, "Test Experiment")
        self.assertEqual(experiment.slug, "test-experiment")
        self.assertEqual(experiment.hypothesis, "test hypothesis")
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)

        changelog = experiment.changes.get()
        self.assertEqual(changelog.changed_by, self.user)
        self.assertEqual(changelog.message, "dev@example.com created Test Experiment")

    def test_invalid_unsluggable_name(self):
        data = {
            "owner": self.user,
            "name": "$.",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], [NimbusUIConstants.ERROR_NAME_INVALID])

    def test_invalid_duplicate_slug(self):
        NimbusExperimentFactory.create(slug="test-experiment")
        data = {
            "owner": self.user,
            "name": "Test Experiment",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], [NimbusUIConstants.ERROR_SLUG_DUPLICATE])

    def test_invalid_with_placeholder_hypothesis(self):
        data = {
            "owner": self.user,
            "name": "$.",
            "hypothesis": NimbusUIConstants.HYPOTHESIS_PLACEHOLDER,
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["hypothesis"], [NimbusUIConstants.ERROR_HYPOTHESIS_PLACEHOLDER]
        )

    def test_form_creates_default_branches(self):
        data = {
            "owner": self.user,
            "name": "Branched Experiment",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.branches.count(), 2)
        self.assertIsNotNone(experiment.reference_branch)
        self.assertEqual(experiment.reference_branch.name, "Control")

        branch_names = set(experiment.branches.values_list("name", flat=True))
        self.assertIn("Control", branch_names)
        self.assertIn("Treatment A", branch_names)


class TestNimbusExperimentSidebarCloneForm(RequestFormTestCase):
    def test_valid_clone_form_creates_experiment(self):
        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "Cloned Experiment",
            "slug": "cloned-experiment",
        }
        form = NimbusExperimentSidebarCloneForm(
            data, instance=parent_experiment, request=self.request
        )
        changelog_message = form.get_changelog_message()
        self.assertEqual(
            changelog_message,
            f"{self.user} cloned this experiment from Original Experiment",
        )

        self.assertTrue(form.is_valid())

        cloned_experiment = form.save()

        self.assertEqual(cloned_experiment.owner, self.user)
        self.assertEqual(cloned_experiment.name, "Cloned Experiment")
        self.assertEqual(cloned_experiment.slug, "cloned-experiment")
        self.assertEqual(
            cloned_experiment.application, NimbusExperiment.Application.DESKTOP
        )

    def test_invalid_unsluggable_name(self):
        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "$.",
            "slug": "",
        }
        form = NimbusExperimentSidebarCloneForm(
            data, instance=parent_experiment, request=self.request
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], [NimbusUIConstants.ERROR_NAME_INVALID])

    def test_invalid_duplicate_slug(self):
        NimbusExperiment.objects.create(
            owner=self.user,
            name="Cloned Experiment",
            slug="cloned-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "Cloned Experiment.",
            "slug": "cloned-experiment",
        }
        form = NimbusExperimentSidebarCloneForm(
            data, instance=parent_experiment, request=self.request
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["name"], [NimbusUIConstants.ERROR_NAME_MAPS_TO_EXISTING_SLUG]
        )


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


class TestDocumentationLinkCreateForm(RequestFormTestCase):
    def test_valid_form_adds_documentation_link(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[],
        )

        form = DocumentationLinkCreateForm(
            instance=experiment,
            data={
                "name": "new name",
                "hypothesis": "new hypothesis",
                "public_description": "new description",
                "documentation_links-TOTAL_FORMS": "0",
                "documentation_links-INITIAL_FORMS": "0",
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.documentation_links.all().count(), 1)
        self.assertEqual(
            form.get_changelog_message(),
            f"{self.request.user} added a documentation link",
        )


class TestDocumentationLinkDeleteForm(RequestFormTestCase):
    def test_valid_form_deletes_documentation_link(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )

        form = DocumentationLinkDeleteForm(
            instance=experiment,
            data={
                "name": "new name",
                "hypothesis": "new hypothesis",
                "public_description": "new description",
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
                "link_id": documentation_link.id,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.documentation_links.all().count(), 0)
        self.assertEqual(
            form.get_changelog_message(),
            f"{self.request.user} deleted a documentation link",
        )


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


class TestCollaboratorsForm(RequestFormTestCase):
    def test_collaborators_form_updates_subscribers(self):
        experiment = NimbusExperimentFactory.create()
        user1 = UserFactory.create()
        user2 = UserFactory.create()

        form = CollaboratorsForm(
            instance=experiment,
            data={"collaborators": [user1.id, user2.id]},
            request=self.request,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(set(experiment.subscribers.all()), {user1, user2})
        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("updated collaborators", changelog.message)

    def test_collaborators_form_removes_subscribers(self):
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        experiment = NimbusExperimentFactory.create()
        experiment.subscribers.set([user1, user2])

        form = CollaboratorsForm(
            instance=experiment, data={"collaborators": [user1.id]}, request=self.request
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(list(experiment.subscribers.all()), [user1])

    def test_collaborators_form_initial_value(self):
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        experiment = NimbusExperimentFactory.create()
        experiment.subscribers.set([user1, user2])

        form = CollaboratorsForm(instance=experiment, request=self.request)
        self.assertEqual(set(form.fields["collaborators"].initial), {user1, user2})


class TestTagAssignForm(RequestFormTestCase):
    def test_valid_form_assigns_tags(self):
        experiment = NimbusExperimentFactory.create()
        tag1 = TagFactory.create(name="Tag 1")
        tag2 = TagFactory.create(name="Tag 2")

        form = TagAssignForm(
            instance=experiment, data={"tags": [tag1.id, tag2.id]}, request=self.request
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(set(experiment.tags.all()), {tag1, tag2})
        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("updated tags", changelog.message)

    def test_form_removes_tags(self):
        tag1 = TagFactory.create(name="Tag 1")
        tag2 = TagFactory.create(name="Tag 2")
        experiment = NimbusExperimentFactory.create()
        experiment.tags.set([tag1, tag2])

        form = TagAssignForm(
            instance=experiment, data={"tags": [tag1.id]}, request=self.request
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(list(experiment.tags.all()), [tag1])
        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("updated tags", changelog.message)

    def test_form_with_no_tags(self):
        tag1 = TagFactory.create(name="Tag 1")
        experiment = NimbusExperimentFactory.create()
        experiment.tags.set([tag1])

        form = TagAssignForm(instance=experiment, data={"tags": []}, request=self.request)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.tags.count(), 0)
        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("updated tags", changelog.message)

    def test_form_queryset_ordered_by_name(self):
        TagFactory.create(name="Z Tag")
        TagFactory.create(name="A Tag")
        TagFactory.create(name="M Tag")

        experiment = NimbusExperimentFactory.create(tags=[])
        form = TagAssignForm(instance=experiment)

        tag_names = [tag.name for tag in form.fields["tags"].queryset]
        self.assertEqual(tag_names, ["A Tag", "M Tag", "Z Tag"])


class TestRolloutStatusForms(RequestFormTestCase):
    def setUp(self):
        super().setUp()
        self.mock_preview_task = patch(
            "experimenter.nimbus_ui.new.forms."
            "nimbus_synchronize_preview_experiments_in_kinto.apply_async"
        ).start()
        self.mock_allocate_bucket_range = patch(
            "experimenter.experiments.models.NimbusExperiment.allocate_bucket_range"
        ).start()
        self.addCleanup(self.mock_preview_task.stop)
        self.addCleanup(self.mock_allocate_bucket_range.stop)

    @parameterized.expand(
        [
            # Draft -> Preview
            (
                DraftToPreviewRolloutForm,
                NimbusExperiment.Status.DRAFT,
                False,
                NimbusExperiment.Status.PREVIEW,
                None,
                NimbusExperiment.PublishStatus.IDLE,
                False,
                "launched rollout to Preview",
            ),
            # Draft -> Live
            (
                DraftToLiveRolloutForm,
                NimbusExperiment.Status.DRAFT,
                False,
                NimbusExperiment.Status.LIVE,
                None,
                NimbusExperiment.PublishStatus.APPROVED,
                False,
                "launched rollout to Live",
            ),
            # Preview -> Live
            (
                PreviewToLiveRolloutForm,
                NimbusExperiment.Status.PREVIEW,
                False,
                NimbusExperiment.Status.LIVE,
                None,
                NimbusExperiment.PublishStatus.APPROVED,
                False,
                "launched rollout to Live",
            ),
            # Preview -> Draft
            (
                PreviewToDraftRolloutForm,
                NimbusExperiment.Status.PREVIEW,
                False,
                NimbusExperiment.Status.DRAFT,
                None,
                NimbusExperiment.PublishStatus.IDLE,
                False,
                "moved the rollout back to Draft",
            ),
            # Live -> Live
            (
                LiveToUpdateRolloutForm,
                NimbusExperiment.Status.LIVE,
                False,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.PublishStatus.REVIEW,
                False,
                "updated rollout population percentages",
            ),
            # Live -> Paused
            (
                LiveToPausedRolloutForm,
                NimbusExperiment.Status.LIVE,
                False,
                NimbusExperiment.Status.PAUSED,
                None,
                NimbusExperiment.PublishStatus.APPROVED,
                True,
                "paused rollout",
            ),
            # Paused -> Live
            (
                PausedToLiveRolloutForm,
                NimbusExperiment.Status.PAUSED,
                True,
                NimbusExperiment.Status.LIVE,
                None,
                NimbusExperiment.PublishStatus.APPROVED,
                False,
                "resumed rollout to Live",
            ),
        ]
    )
    def test_valid_transition(
        self,
        form_class,
        initial_status,
        initial_is_paused,
        expected_status,
        expected_status_next,
        expected_publish_status,
        expected_is_paused,
        expected_changelog_message,
    ):
        experiment = NimbusExperimentFactory.create(
            status=initial_status,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=initial_is_paused,
            is_rollout=True,
        )
        form = form_class(data={}, instance=experiment, request=self.request)

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, expected_status)
        self.assertEqual(experiment.status_next, expected_status_next)
        self.assertEqual(experiment.publish_status, expected_publish_status)
        self.assertEqual(experiment.is_paused, expected_is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(expected_changelog_message, changelog.message)

    @parameterized.expand(
        [
            # Draft -> Preview cannot start from Preview
            (DraftToPreviewRolloutForm, NimbusExperiment.Status.PREVIEW, False),
            # Draft -> Live cannot start from Preview
            (DraftToLiveRolloutForm, NimbusExperiment.Status.PREVIEW, False),
            # Preview -> Live cannot start from Draft
            (PreviewToLiveRolloutForm, NimbusExperiment.Status.DRAFT, False),
            # Preview -> Draft cannot start from Draft
            (PreviewToDraftRolloutForm, NimbusExperiment.Status.DRAFT, False),
            # Live -> Live cannot start from Paused
            (LiveToUpdateRolloutForm, NimbusExperiment.Status.PAUSED, True),
            # Live -> Paused cannot start from Paused
            (LiveToPausedRolloutForm, NimbusExperiment.Status.PAUSED, True),
            # Paused -> Live cannot start from Live
            (PausedToLiveRolloutForm, NimbusExperiment.Status.LIVE, False),
        ]
    )
    def test_invalid_transition(self, form_class, current_status, is_paused):
        experiment = NimbusExperimentFactory.create(
            status=current_status,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=is_paused,
            is_rollout=True,
        )
        form = form_class(data={}, instance=experiment, request=self.request)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Cannot perform this action: experiment must be in state",
            form.errors["__all__"][0],
        )

    def test_paused_transition_rejected_for_experiment(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
            is_rollout=False,
        )
        form = LiveToPausedRolloutForm(data={}, instance=experiment, request=self.request)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["__all__"],
            [NimbusUIConstants.ERROR_INVALID_PAUSED_TRANSITION],
        )

    def test_draft_to_preview_side_effects(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
            is_rollout=True,
        )
        form = DraftToPreviewRolloutForm(
            data={}, instance=experiment, request=self.request
        )
        self.assertTrue(form.is_valid(), form.errors)

        form.save()

        self.mock_allocate_bucket_range.assert_called_once()
        self.mock_preview_task.assert_called_once_with(countdown=5)

    def test_preview_to_draft_resets_published_dto_and_syncs_preview(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
            is_rollout=True,
            published_dto={"slug": "test-rollout"},
        )
        form = PreviewToDraftRolloutForm(
            data={}, instance=experiment, request=self.request
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertIsNone(experiment.published_dto)
        self.mock_preview_task.assert_called_once_with(countdown=5)

    @patch("experimenter.nimbus_ui.new.forms.metrics")
    def test_review_timing_metric(self, mock_metrics):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED,
            is_rollout=True,
        )
        form = DraftToLiveRolloutForm(data={}, instance=experiment, request=self.request)
        form.required_status_next = NimbusExperiment.Status.LIVE
        form.required_publish_status = NimbusExperiment.PublishStatus.REVIEW

        self.assertTrue(form.is_valid(), form.errors)

        form.save()

        mock_metrics.timing.assert_called_once()
