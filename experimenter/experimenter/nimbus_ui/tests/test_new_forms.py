import datetime
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.models import (
    NimbusBranchFeatureValue,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
)
from experimenter.experiments.tests.factories import (
    NimbusBranchScreenshotFactory,
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusVersionedSchemaFactory,
    TagFactory,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.nimbus_ui.new.forms import (
    CollaboratorsForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    NimbusBranchFeatureValueForm,
    NimbusExperimentCreateForm,
    NimbusExperimentSidebarCloneForm,
    RolloutAudienceForm,
    RolloutFeaturesForm,
    RolloutOverviewForm,
    RolloutPhaseForm,
    RolloutQAStatusForm,
    RolloutRisksForm,
    RolloutScreenshotCreateForm,
    RolloutScreenshotDeleteForm,
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
            "application": NimbusExperiment.Application.DESKTOP,
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
                "application": experiment.application,
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
                "application": experiment.application,
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


class TestNimbusBranchFeatureValueForm(RequestFormTestCase):
    def test_initial_value_empty_when_instance_value_is_none_or_empty_dict(self):
        instance_none = NimbusBranchFeatureValue(value=None)
        form_none = NimbusBranchFeatureValueForm(instance=instance_none)
        self.assertEqual(form_none.fields["value"].initial, "")

        instance_empty = NimbusBranchFeatureValue(value={})
        form_empty = NimbusBranchFeatureValueForm(instance=instance_empty)
        self.assertEqual(form_empty.fields["value"].initial, "")

    def test_initial_value_not_overridden_for_existing_value(self):
        instance = NimbusBranchFeatureValue(value={"foo": "bar"})
        form = NimbusBranchFeatureValueForm(instance=instance)
        self.assertIsNone(form.fields["value"].initial)

    def test_clean_value_defaults_empty_value_to_json_object(self):
        form = NimbusBranchFeatureValueForm(data={"value": ""})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["value"], "{}")

    def test_clean_value_preserves_non_empty_value(self):
        form = NimbusBranchFeatureValueForm(data={"value": '{"enabled": true}'})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["value"], '{"enabled": true}')

    def test_schemas(self):
        feature_with_schema = NimbusFeatureConfigFactory.create(
            name="with-schema",
            application=NimbusExperiment.Application.IOS,
            schemas=[NimbusVersionedSchemaFactory.build(version=None)],
        )

        feature_without_schema = NimbusFeatureConfigFactory.create(
            name="without-schema",
            application=NimbusExperiment.Application.IOS,
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.IOS,
            feature_configs=[feature_with_schema, feature_without_schema],
        )

        forms = {
            fv.feature_config.slug: NimbusBranchFeatureValueForm(instance=fv)
            for fv in experiment.reference_branch.feature_values.all()
        }

        self.assertEqual(
            forms["with-schema"].fields["value"].widget.attrs["data-experiment-slug"],
            experiment.slug,
        )
        self.assertEqual(
            forms["with-schema"].fields["value"].widget.attrs["data-feature-slug"],
            feature_with_schema.slug,
        )
        self.assertEqual(
            json.loads(forms["with-schema"].fields["value"].widget.attrs["data-schema"]),
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "description": (
                    "Fake schema that matches NimbusBranchFactory feature_value factory"
                ),
                "type": "object",
                "patternProperties": {"^.*$": {"type": "string"}},
                "additionalProperties": False,
            },
        )
        self.assertNotIn(
            "data-schema", forms["without-schema"].fields["value"].widget.attrs
        )


class TestRolloutFeaturesForm(RequestFormTestCase):
    def test_feature_config_choices_use_name_and_description(self):
        feature_config = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            name="Rollout feature",
            description="Rollout feature description",
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )

        form = RolloutFeaturesForm(instance=experiment, request=self.request)
        rendered_field = str(form["feature_configs"])

        self.assertIn("Rollout feature", rendered_field)
        self.assertIn('data-subtext="Rollout feature description"', rendered_field)

    def test_form_sets_initial_rollout_experience_and_filters_feature_configs(self):
        desktop_feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="desktop-rollout-feature",
        )
        # Add a feature config for a different application to verify that the form
        # filters it out
        NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.IOS,
            slug="ios-rollout-feature",
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            takeaways_summary="Existing rollout experience",
            feature_configs=[desktop_feature],
        )

        form = RolloutFeaturesForm(instance=experiment, request=self.request)

        self.assertEqual(
            form.fields["rollout_experience"].initial,
            "Existing rollout experience",
        )
        self.assertIn(desktop_feature, form.fields["feature_configs"].queryset)
        self.assertTrue(
            all(
                feature_config.application == NimbusExperiment.Application.DESKTOP
                for feature_config in form.fields["feature_configs"].queryset
            )
        )

    def test_form_reports_branch_feature_value_errors(self):
        feature_config = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="rollout-feature-invalid",
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
        )
        experiment.reference_branch.screenshots.all().delete()

        form = RolloutFeaturesForm(
            instance=experiment,
            data={
                "rollout_experience": "Updated rollout experience",
                "feature_configs": [feature_config.id],
                "branch-feature-value-TOTAL_FORMS": "1",
                "branch-feature-value-INITIAL_FORMS": "1",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "branch-feature-value-0-value": "{}",
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
            },
            request=self.request,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("branch_feature_values", form.errors)
        self.assertEqual(
            form.errors["branch_feature_values"],
            [{"id": ["This field is required."]}],
        )

    def test_form_saves_new_reference_branch_feature_values(self):
        feature_config1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="rollout-feature-1",
        )
        feature_config2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="rollout-feature-2",
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
            takeaways_summary="",
        )

        form = RolloutFeaturesForm(
            instance=experiment,
            data={
                "rollout_experience": "Updated rollout experience",
                "feature_configs": [feature_config1.id, feature_config2.id],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        experiment.refresh_from_db()

        self.assertEqual(experiment.takeaways_summary, "Updated rollout experience")
        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertEqual(
            set(
                experiment.reference_branch.feature_values.values_list(
                    "feature_config", flat=True
                )
            ),
            {feature_config1.id, feature_config2.id},
        )
        self.assertEqual(
            experiment.changes.latest("changed_on").message,
            f"{self.user} updated rollout features",
        )

    def test_form_deletes_removed_reference_branch_feature_values(self):
        feature_config = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="rollout-feature-delete",
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config],
            takeaways_summary="Existing rollout experience",
        )

        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature_config
        )

        form = RolloutFeaturesForm(
            instance=experiment,
            data={
                "rollout_experience": "Updated rollout experience",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "1",
                "branch-feature-value-INITIAL_FORMS": "1",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "branch-feature-value-0-id": reference_feature_value.id,
                "branch-feature-value-0-value": reference_feature_value.value,
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        experiment.refresh_from_db()

        self.assertEqual(experiment.takeaways_summary, "Updated rollout experience")
        self.assertEqual(experiment.feature_configs.count(), 0)
        self.assertFalse(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config
            ).exists()
        )
        self.assertEqual(
            experiment.changes.latest("changed_on").message,
            f"{self.user} updated rollout features",
        )

    def test_form_uploads_rollout_screenshots_to_reference_branch(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
            takeaways_summary="",
        )
        experiment.reference_branch.screenshots.all().delete()

        image = NimbusBranchScreenshotFactory.build().image
        form = RolloutFeaturesForm(
            instance=experiment,
            data={
                "rollout_experience": "Updated rollout experience",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-TOTAL_FORMS": "1",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-0-description": "Test description",
            },
            files={"rollout-screenshots-0-image": image},
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        experiment.refresh_from_db()

        screenshots = experiment.reference_branch.screenshots.all()
        self.assertEqual(screenshots.count(), 1)
        self.assertTrue(screenshots.first().image)
        self.assertEqual(screenshots.first().description, "Test description")

    def test_form_supports_multiple_rollout_screenshots(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
            takeaways_summary="",
        )
        experiment.reference_branch.screenshots.all().delete()

        first_image = NimbusBranchScreenshotFactory.build().image
        second_image = NimbusBranchScreenshotFactory.build().image
        form = RolloutFeaturesForm(
            instance=experiment,
            data={
                "rollout_experience": "Updated rollout experience",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-TOTAL_FORMS": "2",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-0-description": "First",
                "rollout-screenshots-1-description": "Second",
            },
            files={
                "rollout-screenshots-0-image": first_image,
                "rollout-screenshots-1-image": second_image,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        experiment.refresh_from_db()

        self.assertEqual(experiment.reference_branch.screenshots.count(), 2)

    def test_form_reports_rollout_screenshot_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
        )
        experiment.reference_branch.screenshots.all().delete()

        form = RolloutFeaturesForm(
            instance=experiment,
            data={
                "rollout_experience": "",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-TOTAL_FORMS": "1",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-0-description": "Not a real image",
            },
            files={
                "rollout-screenshots-0-image": SimpleUploadedFile(
                    "bad.png", b"this is not an image", content_type="image/png"
                )
            },
            request=self.request,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("rollout_screenshots", form.errors)


class TestRolloutScreenshotCreateForm(RequestFormTestCase):
    def test_form_creates_empty_screenshot_and_logs_change(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment.reference_branch.screenshots.all().delete()

        form = RolloutScreenshotCreateForm(
            instance=experiment,
            data={
                "rollout_experience": "",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(experiment.reference_branch.screenshots.count(), 1)
        self.assertEqual(
            experiment.changes.latest("changed_on").message,
            f"{self.user} added a rollout screenshot",
        )


class TestRolloutScreenshotDeleteForm(RequestFormTestCase):
    def test_form_deletes_screenshot_and_logs_change(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment.reference_branch.screenshots.all().delete()
        screenshot = NimbusBranchScreenshotFactory.create(
            branch=experiment.reference_branch
        )

        form = RolloutScreenshotDeleteForm(
            instance=experiment,
            data={
                "screenshot_id": screenshot.id,
                "rollout_experience": "",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "branch-feature-value-MIN_NUM_FORMS": "0",
                "branch-feature-value-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-TOTAL_FORMS": "1",
                "rollout-screenshots-INITIAL_FORMS": "1",
                "rollout-screenshots-MIN_NUM_FORMS": "0",
                "rollout-screenshots-MAX_NUM_FORMS": "1000",
                "rollout-screenshots-0-id": screenshot.id,
                "rollout-screenshots-0-description": screenshot.description,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(experiment.reference_branch.screenshots.count(), 0)
        self.assertEqual(
            experiment.changes.latest("changed_on").message,
            f"{self.user} removed a rollout screenshot",
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


class TestRolloutPhaseForm(TestCase):
    def test_end_date_before_start_date_is_invalid(self):
        form = RolloutPhaseForm(
            data={
                "start_date": "2026-02-01",
                "end_date": "2026-01-01",
                "population_percent": "10",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            NimbusUIConstants.ERROR_ROLLOUT_PHASE_DATE_ORDER,
            form.errors["end_date"],
        )

    def test_end_date_equal_to_start_date_is_valid(self):
        form = RolloutPhaseForm(
            data={
                "start_date": "2026-01-01",
                "end_date": "2026-01-01",
                "population_percent": "10",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_dates_optional_so_blank_is_valid(self):
        form = RolloutPhaseForm(data={"population_percent": "10"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_start_date_without_end_date_is_invalid(self):
        form = RolloutPhaseForm(data={"start_date": "2026-01-15"})
        self.assertFalse(form.is_valid())
        self.assertIn(
            NimbusUIConstants.ERROR_ROLLOUT_PHASE_DATE_INCOMPLETE,
            form.errors["end_date"],
        )

    def test_end_date_without_start_date_is_invalid(self):
        form = RolloutPhaseForm(data={"end_date": "2026-01-15"})
        self.assertFalse(form.is_valid())
        self.assertIn(
            NimbusUIConstants.ERROR_ROLLOUT_PHASE_DATE_INCOMPLETE,
            form.errors["start_date"],
        )

    def test_population_over_100_is_invalid(self):
        form = RolloutPhaseForm(data={"population_percent": "150"})
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)

    def test_population_100_is_valid(self):
        form = RolloutPhaseForm(data={"population_percent": "100"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_negative_population_percent_is_invalid(self):
        form = RolloutPhaseForm(data={"population_percent": "-1"})
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)

    def test_population_percent_over_100_is_invalid(self):
        form = RolloutPhaseForm(data={"population_percent": "101"})
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)
