import datetime
import decimal
import json

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.test import TestCase

from experimenter.experiments.forms import (
    BugzillaURLField,
    ChangeLogMixin,
    ExperimentArchiveForm,
    ExperimentCommentForm,
    ExperimentObjectivesForm,
    ExperimentOverviewForm,
    ExperimentReviewForm,
    ExperimentRisksForm,
    ExperimentStatusForm,
    ExperimentVariantAddonForm,
    ExperimentVariantPrefForm,
    ExperimentVariantsAddonForm,
    ExperimentVariantsFormSet,
    ExperimentVariantsPrefForm,
    JSONField,
    NameSlugMixin,
)
from experimenter.experiments.models import Experiment, ExperimentVariant
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.tests.mixins import (
    MockBugzillaMixin,
    MockMailMixin,
    MockTasksMixin,
    MockRequestMixin,
)


class TestJSONField(TestCase):

    def test_jsonfield_accepts_valid_json(self):
        valid_json = json.dumps({"a": True, 2: ["b", 3, 4.0]})
        field = JSONField()
        cleaned = field.clean(valid_json)
        self.assertEqual(cleaned, valid_json)

    def test_jsonfield_rejects_invalid_json(self):
        invalid_json = "{this isnt valid"
        field = JSONField()

        with self.assertRaises(ValidationError):
            field.clean(invalid_json)


class TestBugzillaURLField(TestCase):

    def test_accepts_bugzilla_url(self):
        field = BugzillaURLField()
        bugzilla_url = "{base}/123/".format(base=field.BUGZILLA_BASE_URL)
        cleaned = field.clean(bugzilla_url)
        self.assertEqual(cleaned, bugzilla_url)

    def test_rejects_non_bugzilla_url(self):
        field = BugzillaURLField()

        with self.assertRaises(ValidationError):
            field.clean("www.example.com")


class TestNameSlugMixin(TestCase):

    def test_name_slug_mixin_creates_slug_from_name(self):

        class TestForm(NameSlugMixin, forms.Form):
            name = forms.CharField()
            slug = forms.CharField(required=False)

        name = "A Name"
        expected_slug = "a-name"

        form = TestForm({"name": name})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], name)
        self.assertEqual(form.cleaned_data["slug"], expected_slug)


class TestExperimentVariantAddonForm(TestCase):

    def test_form_creates_variant(self):
        experiment = ExperimentFactory.create()

        data = {
            "description": "Its the control! So controlly.",
            "experiment": experiment.id,
            "is_control": True,
            "name": "The Control Variant",
            "ratio": 50,
        }

        form = ExperimentVariantAddonForm(data)

        self.assertTrue(form.is_valid())

        saved_variant = form.save()
        variant = ExperimentVariant.objects.get(id=saved_variant.id)

        self.assertEqual(variant.experiment.id, experiment.id)
        self.assertTrue(variant.is_control)
        self.assertEqual(variant.description, data["description"])
        self.assertEqual(variant.name, data["name"])
        self.assertEqual(variant.ratio, data["ratio"])
        self.assertEqual(variant.slug, "the-control-variant")


class TestExperimentVariantPrefForm(TestCase):

    def test_form_creates_variant(self):
        experiment = ExperimentFactory.create()

        data = {
            "description": "Its the control! So controlly.",
            "experiment": experiment.id,
            "is_control": True,
            "name": "The Control Variant",
            "ratio": 50,
            "value": "true",
        }

        form = ExperimentVariantPrefForm(data)

        self.assertTrue(form.is_valid())

        saved_variant = form.save()
        variant = ExperimentVariant.objects.get(id=saved_variant.id)

        self.assertEqual(variant.experiment.id, experiment.id)
        self.assertTrue(variant.is_control)
        self.assertEqual(variant.description, data["description"])
        self.assertEqual(variant.name, data["name"])
        self.assertEqual(variant.ratio, data["ratio"])
        self.assertEqual(variant.slug, "the-control-variant")
        self.assertEqual(variant.value, "true")


class TestChangeLogMixin(MockRequestMixin, TestCase):

    def test_mixin_creates_change_log_with_request_user_on_save(self):

        class TestForm(ChangeLogMixin, forms.ModelForm):

            class Meta:
                model = Experiment
                fields = ("name",)

        data = ExperimentFactory.attributes()
        form = TestForm(request=self.request, data=data)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.changes.count(), 1)

        change = experiment.changes.get()
        self.assertEqual(change.changed_by, self.user)

    def test_mixin_sets_old_and_new_status(self):
        old_status = Experiment.STATUS_DRAFT
        new_status = Experiment.STATUS_REVIEW
        experiment = ExperimentFactory.create_with_status(old_status)

        self.assertEqual(experiment.changes.count(), 1)

        class TestForm(ChangeLogMixin, forms.ModelForm):

            class Meta:
                model = Experiment
                fields = ("status",)

        form = TestForm(
            request=self.request,
            data={"status": new_status},
            instance=experiment,
        )
        self.assertTrue(form.is_valid())

        form.save()

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.old_status, old_status)
        self.assertEqual(change.new_status, new_status)


class TestExperimentOverviewForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.data = {
            "type": Experiment.TYPE_PREF,
            "owner": self.user.id,
            "name": "A new experiment!",
            "short_description": "Let us learn new things",
            "data_science_bugzilla_url": "https://bugzilla.mozilla.org/123/",
            "feature_bugzilla_url": "https://bugzilla.mozilla.org/123/",
            "related_work": "Designs: https://www.example.com/myproject/",
            "proposed_start_date": datetime.date.today(),
            "proposed_end_date": (
                datetime.date.today() + datetime.timedelta(days=1)
            ),
        }

    def test_form_creates_experiment(self):
        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.status, experiment.STATUS_DRAFT)
        self.assertEqual(experiment.name, self.data["name"])
        self.assertEqual(experiment.slug, "a-new-experiment")
        self.assertEqual(
            experiment.short_description, self.data["short_description"]
        )
        self.assertEqual(
            experiment.proposed_start_date, self.data["proposed_start_date"]
        )
        self.assertEqual(
            experiment.proposed_end_date, self.data["proposed_end_date"]
        )

        self.assertEqual(experiment.changes.count(), 1)
        change = experiment.changes.get()
        self.assertEqual(change.old_status, None)
        self.assertEqual(change.new_status, experiment.status)
        self.assertEqual(change.changed_by, self.request.user)


class TestExperimentVariantsFormSet(TestCase):

    def setUp(self):
        self.FormSet = inlineformset_factory(
            formset=ExperimentVariantsFormSet,
            model=ExperimentVariant,
            parent_model=Experiment,
            fields=["is_control", "ratio", "name", "slug", "description"],
        )

        self.data = {
            "variants-TOTAL_FORMS": "3",
            "variants-INITIAL_FORMS": "0",
            "variants-MIN_NUM_FORMS": "0",
            "variants-MAX_NUM_FORMS": "1000",
            "variants-0-is_control": True,
            "variants-0-ratio": "34",
            "variants-0-name": "control name",
            "variants-0-slug": "control-slug",
            "variants-0-description": "control desc",
            "variants-1-is_control": False,
            "variants-1-ratio": "33",
            "variants-1-name": "branch 1 name",
            "variants-1-slug": "branch-1-slug",
            "variants-1-description": "branch 1 desc",
            "variants-2-is_control": False,
            "variants-2-ratio": "33",
            "variants-2-name": "branch 2 name",
            "variants-2-slug": "branch-2-slug",
            "variants-2-description": "branch 2 desc",
        }

    def test_formset_valid_if_sizes_sum_to_100(self):
        formset = self.FormSet(data=self.data)
        self.assertTrue(formset.is_valid())

    def test_formset_invalid_if_sizes_sum_to_less_than_100(self):
        self.data["variants-0-ratio"] = 30
        formset = self.FormSet(data=self.data)
        self.assertFalse(formset.is_valid())

        for form in formset.forms:
            self.assertIn("ratio", form.errors)

    def test_formset_invalid_if_sizes_sum_to_more_than_100(self):
        self.data["variants-0-ratio"] = 40
        formset = self.FormSet(data=self.data)
        self.assertFalse(formset.is_valid())

        for form in formset.forms:
            self.assertIn("ratio", form.errors)

    def test_formset_invalid_if_duplicate_slugs_appear(self):
        self.data["variants-0-slug"] = self.data["variants-1-slug"]
        formset = self.FormSet(data=self.data)
        self.assertFalse(formset.is_valid())

        for form in formset.forms:
            self.assertIn("name", form.errors)


class TestExperimentVariantsAddonForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )

        self.data = {
            "population_percent": "10",
            "firefox_version": Experiment.VERSION_CHOICES[-1][0],
            "firefox_channel": Experiment.CHANNEL_NIGHTLY,
            "client_matching": "en-us only please",
            "variants-TOTAL_FORMS": "3",
            "variants-INITIAL_FORMS": "0",
            "variants-MIN_NUM_FORMS": "0",
            "variants-MAX_NUM_FORMS": "1000",
            "variants-0-is_control": True,
            "variants-0-ratio": "34",
            "variants-0-name": "control name",
            "variants-0-description": "control desc",
            "variants-1-is_control": False,
            "variants-1-ratio": "33",
            "variants-1-name": "branch 1 name",
            "variants-1-description": "branch 1 desc",
            "variants-2-is_control": False,
            "variants-2-ratio": "33",
            "variants-2-name": "branch 2 name",
            "variants-2-description": "branch 2 desc",
        }

    def test_form_is_invalid_if_population_percent_is_0(self):
        self.data["population_percent"] = "0"
        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data
        )
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)

    def test_form_is_invalid_if_population_percent_below_0(self):
        self.data["population_percent"] = "-1"
        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data
        )
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)

    def test_form_is_invalid_if_population_percent_above_100(self):
        self.data["population_percent"] = "101"
        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data
        )
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)

    def test_form_saves_new_variants(self):
        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)

        experiment = form.save()

        self.assertEqual(
            experiment.population_percent, decimal.Decimal("10.000")
        )
        self.assertEqual(
            experiment.firefox_version, self.data["firefox_version"]
        )
        self.assertEqual(
            experiment.firefox_channel, self.data["firefox_channel"]
        )
        self.assertEqual(
            experiment.client_matching, self.data["client_matching"]
        )

        self.assertEqual(experiment.variants.count(), 3)

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.assertTrue(branch0.is_control)
        self.assertEqual(branch0.ratio, 34)
        self.assertEqual(
            branch0.description, self.data["variants-0-description"]
        )

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.assertFalse(branch1.is_control)
        self.assertEqual(branch1.ratio, 33)
        self.assertEqual(
            branch1.description, self.data["variants-1-description"]
        )

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.assertFalse(branch2.is_control)
        self.assertEqual(branch2.ratio, 33)
        self.assertEqual(
            branch2.description, self.data["variants-2-description"]
        )

    def test_form_edits_existing_variants(self):
        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        self.data["variants-INITIAL_FORMS"] = 3

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.data["variants-0-id"] = branch0.id
        self.data["variants-0-DELETE"] = False
        self.data["variants-0-name"] = "new branch 0 name"
        self.data["variants-0-description"] = "new branch 0 description"

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.data["variants-1-id"] = branch1.id
        self.data["variants-1-DELETE"] = False
        self.data["variants-1-name"] = "new branch 1 name"
        self.data["variants-1-description"] = "new branch 1 description"

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.data["variants-2-id"] = branch2.id
        self.data["variants-2-DELETE"] = False
        self.data["variants-2-name"] = "new branch 2 name"
        self.data["variants-2-description"] = "new branch 2 description"

        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.assertTrue(branch0.is_control)
        self.assertEqual(branch0.ratio, 34)
        self.assertEqual(
            branch0.description, self.data["variants-0-description"]
        )

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.assertFalse(branch1.is_control)
        self.assertEqual(branch1.ratio, 33)
        self.assertEqual(
            branch1.description, self.data["variants-1-description"]
        )

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.assertFalse(branch2.is_control)
        self.assertEqual(branch2.ratio, 33)
        self.assertEqual(
            branch2.description, self.data["variants-2-description"]
        )

    def test_form_adds_new_variant(self):
        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        self.data["variants-INITIAL_FORMS"] = 3
        self.data["variants-TOTAL_FORMS"] = 4

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.data["variants-0-id"] = branch0.id
        self.data["variants-0-ratio"] = 25

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.data["variants-1-id"] = branch1.id
        self.data["variants-1-ratio"] = 25

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.data["variants-2-id"] = branch2.id
        self.data["variants-2-ratio"] = 25

        self.data["variants-3-DELETE"] = False
        self.data["variants-3-name"] = "new branch 0 name"
        self.data["variants-3-description"] = "new branch 0 description"
        self.data["variants-3-ratio"] = 25

        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 4)

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.assertEqual(branch0.ratio, 25)

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.assertEqual(branch1.ratio, 25)

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.assertEqual(branch2.ratio, 25)

        branch3 = experiment.variants.get(name=self.data["variants-3-name"])
        self.assertEqual(branch3.ratio, 25)
        self.assertEqual(
            branch3.description, self.data["variants-3-description"]
        )

    def test_form_removes_variant(self):
        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        self.data["variants-INITIAL_FORMS"] = 3
        self.data["variants-TOTAL_FORMS"] = 3

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.data["variants-0-id"] = branch0.id
        self.data["variants-0-ratio"] = 50

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.data["variants-1-id"] = branch1.id
        self.data["variants-1-DELETE"] = True

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.data["variants-2-id"] = branch2.id
        self.data["variants-2-ratio"] = 50

        form = ExperimentVariantsAddonForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 2)

        self.assertTrue(
            experiment.variants.filter(
                name=self.data["variants-0-name"]
            ).exists()
        )
        self.assertFalse(
            experiment.variants.filter(
                name=self.data["variants-1-name"]
            ).exists()
        )
        self.assertTrue(
            experiment.variants.filter(
                name=self.data["variants-2-name"]
            ).exists()
        )


class TestExperimentVariantsPrefForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.branch0_name = "control name"
        self.branch1_name = "branch 1 name"
        self.branch2_name = "branch 2 name"

        self.data = {
            "population_percent": "10",
            "firefox_version": Experiment.VERSION_CHOICES[-1][0],
            "firefox_channel": Experiment.CHANNEL_NIGHTLY,
            "client_matching": "en-us only please",
            "pref_key": "browser.test.example",
            "pref_type": Experiment.PREF_TYPE_STR,
            "pref_branch": Experiment.PREF_BRANCH_DEFAULT,
            "variants-TOTAL_FORMS": "3",
            "variants-INITIAL_FORMS": "0",
            "variants-MIN_NUM_FORMS": "0",
            "variants-MAX_NUM_FORMS": "1000",
            "variants-0-is_control": True,
            "variants-0-ratio": "34",
            "variants-0-name": self.branch0_name,
            "variants-0-description": "control desc",
            "variants-0-value": '"control value"',
            "variants-1-is_control": False,
            "variants-1-ratio": "33",
            "variants-1-name": self.branch1_name,
            "variants-1-description": "branch 1 desc",
            "variants-1-value": '"branch 1 value"',
            "variants-2-is_control": False,
            "variants-2-ratio": "33",
            "variants-2-name": self.branch2_name,
            "variants-2-description": "branch 2 desc",
            "variants-2-value": '"branch 2 value"',
        }

    def test_form_saves_variants(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )

        form = ExperimentVariantsPrefForm(
            request=self.request, data=self.data, instance=created_experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        branch0 = experiment.variants.get(name=self.branch0_name)
        self.assertTrue(branch0.is_control)
        self.assertEqual(branch0.ratio, 34)
        self.assertEqual(
            branch0.description, self.data["variants-0-description"]
        )
        self.assertEqual(branch0.value, self.data["variants-0-value"])

        branch1 = experiment.variants.get(name=self.branch1_name)
        self.assertFalse(branch1.is_control)
        self.assertEqual(branch1.ratio, 33)
        self.assertEqual(
            branch1.description, self.data["variants-1-description"]
        )
        self.assertEqual(branch1.value, self.data["variants-1-value"])

        branch2 = experiment.variants.get(name=self.branch2_name)
        self.assertFalse(branch2.is_control)
        self.assertEqual(branch2.ratio, 33)
        self.assertEqual(
            branch2.description, self.data["variants-2-description"]
        )
        self.assertEqual(branch2.value, self.data["variants-2-value"])


class TestExperimentObjectivesForm(MockRequestMixin, TestCase):

    def test_form_saves_objectives(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )

        data = {
            "objectives": "The objective is to experiment!",
            "analysis_owner": "Jim Bob The Data Scientist",
            "analysis": "Lets analyze the results!",
        }

        form = ExperimentObjectivesForm(
            request=self.request, data=data, instance=created_experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.objectives, data["objectives"])
        self.assertEqual(experiment.analysis, data["analysis"])


class TestExperimentRisksForm(MockRequestMixin, TestCase):

    def test_form_saves_risks(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )

        data = {
            "risk_partner_related": True,
            "risk_brand": True,
            "risk_fast_shipped": True,
            "risk_confidential": True,
            "risk_release_population": True,
            "risks": "There are some risks",
            "testing": "Always be sure to test!",
        }

        form = ExperimentRisksForm(
            request=self.request, data=data, instance=created_experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.assertTrue(experiment.risk_partner_related)
        self.assertTrue(experiment.risk_brand)
        self.assertTrue(experiment.risk_fast_shipped)
        self.assertTrue(experiment.risk_confidential)
        self.assertTrue(experiment.risk_release_population)
        self.assertEqual(experiment.risks, data["risks"])
        self.assertEqual(experiment.testing, data["testing"])


class TestExperimentReviewForm(
    MockRequestMixin, MockBugzillaMixin, MockTasksMixin, TestCase
):

    def test_form_saves_reviews(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW
        )

        self.assertFalse(experiment.review_science)
        self.assertFalse(experiment.review_peer)
        self.assertFalse(experiment.review_relman)
        self.assertFalse(experiment.review_qa)
        self.assertFalse(experiment.review_legal)
        self.assertFalse(experiment.review_ux)
        self.assertFalse(experiment.review_security)
        self.assertFalse(experiment.review_vp)
        self.assertFalse(experiment.review_data_steward)

        data = {
            "review_science": True,
            "review_peer": True,
            "review_relman": True,
            "review_qa": True,
            "review_legal": True,
            "review_ux": True,
            "review_security": True,
            "review_vp": True,
            "review_data_steward": True,
        }

        form = ExperimentReviewForm(
            request=self.request, data=data, instance=experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.assertTrue(experiment.review_science)
        self.assertTrue(experiment.review_peer)
        self.assertTrue(experiment.review_relman)
        self.assertTrue(experiment.review_qa)
        self.assertTrue(experiment.review_legal)
        self.assertTrue(experiment.review_ux)
        self.assertTrue(experiment.review_security)
        self.assertTrue(experiment.review_vp)
        self.assertTrue(experiment.review_data_steward)

    def test_added_reviews_property(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW
        )

        data = {"review_peer": True, "review_science": True}

        form = ExperimentReviewForm(
            request=self.request, data=data, instance=experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(len(form.added_reviews), 2)
        self.assertEqual(len(form.removed_reviews), 0)
        self.assertIn(form.fields["review_peer"].label, form.added_reviews)
        self.assertIn(form.fields["review_science"].label, form.added_reviews)

    def test_removed_reviews_property(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, review_peer=True, review_science=True
        )

        data = {"review_peer": False, "review_science": False}

        form = ExperimentReviewForm(
            request=self.request, data=data, instance=experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(len(form.added_reviews), 0)
        self.assertEqual(len(form.removed_reviews), 2)
        self.assertIn(form.fields["review_peer"].label, form.removed_reviews)
        self.assertIn(
            form.fields["review_science"].label, form.removed_reviews
        )


class TestExperimentStatusForm(
    MockMailMixin,
    MockBugzillaMixin,
    MockRequestMixin,
    MockTasksMixin,
    TestCase,
):

    def test_form_allows_valid_state_transition_and_creates_changelog(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_REVIEW},
            instance=experiment,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.assertEqual(experiment.status, experiment.STATUS_REVIEW)
        change = experiment.changes.latest()
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_REVIEW)

    def test_form_rejects_invalid_state_transitions(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_LIVE},
            instance=experiment,
        )
        self.assertFalse(form.is_valid())

    def test_sends_review_mail_when_draft_becomes_review(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_REVIEW},
            instance=experiment,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.mock_tasks_review_email.delay.assert_called_with(
            self.user.id, experiment.name, experiment.experiment_url, False
        )

    def test_sets_bugzilla_id_when_draft_becomes_review(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_REVIEW},
            instance=experiment,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.mock_tasks_create_bug.delay.assert_called_with(
            self.user.id, experiment.id
        )

    def test_adds_bugzilla_comment_when_review_becomes_ship(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, bugzilla_id="12345"
        )
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_SHIP},
            instance=experiment,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.mock_tasks_add_comment.delay.assert_called_with(
            self.user.id, experiment.id
        )


class TestExperimentCommentForm(MockRequestMixin, TestCase):

    def test_form_creates_comment(self):
        text = "hello"
        section = Experiment.SECTION_OVERVIEW
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        form = ExperimentCommentForm(
            request=self.request,
            data={
                "experiment": experiment.id,
                "section": section,
                "text": text,
            },
        )
        self.assertTrue(form.is_valid())
        comment = form.save()
        self.assertEqual(comment.experiment, experiment)
        self.assertEqual(comment.section, section)
        self.assertEqual(comment.created_by, self.user)
        self.assertEqual(comment.text, text)

    def test_section_must_be_valid(self):
        text = "hello"
        section = "invalid section"
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        form = ExperimentCommentForm(
            request=self.request,
            data={
                "experiment": experiment.id,
                "section": section,
                "text": text,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("section", form.errors)

    def test_text_is_required(self):
        text = ""
        section = Experiment.SECTION_OVERVIEW
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        form = ExperimentCommentForm(
            request=self.request,
            data={
                "experiment": experiment.id,
                "section": section,
                "text": text,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)


class TestExperimentArchiveForm(MockRequestMixin, TestCase):

    def test_form_flips_archive_bool(self):
        experiment = ExperimentFactory.create(archived=False)

        form = ExperimentArchiveForm(
            self.request, instance=experiment, data={}
        )
        self.assertTrue(form.is_valid())

        experiment = form.save()
        self.assertTrue(experiment.archived)

        form = ExperimentArchiveForm(
            self.request, instance=experiment, data={}
        )
        self.assertTrue(form.is_valid())

        experiment = form.save()
        self.assertFalse(experiment.archived)
