import datetime
import decimal
import json

import mock
from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
)
from experimenter.experiments.forms import (
    ChangeLogMixin,
    ControlVariantForm,
    ExperimentObjectivesForm,
    ExperimentOverviewForm,
    ExperimentRisksForm,
    ExperimentVariantsForm,
    ExperimentalVariantForm,
    JSONField,
    NameSlugMixin,
)
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.projects.tests.factories import ProjectFactory


class TestJSONField(TestCase):

    def test_jsonfield_accepts_valid_json(self):
        valid_json = json.dumps({'a': True, 2: ['b', 3, 4.0]})
        field = JSONField()
        cleaned = field.clean(valid_json)
        self.assertEqual(cleaned, valid_json)

    def test_jsonfield_rejects_invalid_json(self):
        invalid_json = '{this isnt valid'
        field = JSONField()

        with self.assertRaises(ValidationError):
            field.clean(invalid_json)


class TestNameSlugMixin(TestCase):

    def test_name_slug_mixin_creates_slug_from_name(self):
        class TestForm(NameSlugMixin, forms.Form):
            name = forms.CharField()
            slug = forms.CharField(required=False)

        name = 'A Name'
        expected_slug = 'a-name'

        form = TestForm({'name': name})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], name)
        self.assertEqual(form.cleaned_data['slug'], expected_slug)


class TestControlVariantForm(TestCase):

    def test_form_creates_control_variant(self):
        experiment = ExperimentFactory.create()

        data = {
            'experiment': experiment.id,
            'name': 'The Control Variant',
            'description': 'Its the control! So controlly.',
            'ratio': 50,
            'value': 'true',
        }

        prefixed_data = {
            '{}-{}'.format(ControlVariantForm.prefix, key): value
            for key, value in data.items()
        }

        form = ControlVariantForm(prefixed_data)

        self.assertTrue(form.is_valid())

        saved_variant = form.save()
        variant = ExperimentVariant.objects.get(id=saved_variant.id)

        self.assertEqual(variant.experiment.id, experiment.id)
        self.assertTrue(variant.is_control)
        self.assertEqual(variant.name, data['name'])
        self.assertEqual(variant.description, data['description'])
        self.assertEqual(variant.slug, 'the-control-variant')
        self.assertEqual(variant.ratio, data['ratio'])
        self.assertEqual(variant.value, 'true')


class TestExperimentalVariantForm(TestCase):

    def test_form_creates_experimental_variant(self):
        experiment = ExperimentFactory.create()

        data = {
            'experiment': experiment.id,
            'name': 'The Experimental Variant',
            'description': 'Its the experimental! So experimentally.',
            'ratio': 50,
            'value': 'false',
        }

        prefixed_data = {
            '{}-{}'.format(ExperimentalVariantForm.prefix, key): value
            for key, value in data.items()
        }

        form = ExperimentalVariantForm(prefixed_data)

        self.assertTrue(form.is_valid())

        saved_variant = form.save()
        variant = ExperimentVariant.objects.get(id=saved_variant.id)

        self.assertEqual(variant.experiment.id, experiment.id)
        self.assertFalse(variant.is_control)
        self.assertEqual(variant.name, data['name'])
        self.assertEqual(variant.description, data['description'])
        self.assertEqual(variant.slug, 'the-experimental-variant')
        self.assertEqual(variant.ratio, data['ratio'])
        self.assertEqual(variant.value, 'false')


class MockRequestMixin(object):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.request = mock.Mock()
        self.request.user = self.user


class TestChangeLogMixin(MockRequestMixin, TestCase):

    def test_mixin_creates_change_log_with_request_user_on_save(self):
        class TestForm(ChangeLogMixin, forms.ModelForm):

            class Meta:
                model = Experiment
                fields = ('name',)

        data = ExperimentFactory.attributes()
        form = TestForm(request=self.request, data=data)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.changes.count(), 1)

        change = experiment.changes.get()
        self.assertEqual(change.changed_by, self.user)

    def test_mixin_sets_old_and_new_status(self):
        old_status = Experiment.STATUS_CREATED
        new_status = Experiment.STATUS_PENDING
        experiment = ExperimentFactory.create_with_status(old_status)

        self.assertEqual(experiment.changes.count(), 1)

        class TestForm(ChangeLogMixin, forms.ModelForm):

            class Meta:
                model = Experiment
                fields = ('status',)

        form = TestForm(
            request=self.request,
            data={'status': new_status},
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

        self.project = ProjectFactory.create()

        self.data = {
            'project': self.project.id,
            'name': 'A new experiment!',
            'short_description': 'Let us learn new things',
            'population_percent': '10',
            'firefox_version': Experiment.VERSION_CHOICES[-1][0],
            'firefox_channel': Experiment.CHANNEL_NIGHTLY,
            'client_matching': 'en-us only please',
            'proposed_start_date': datetime.date.today(),
            'proposed_end_date': (
                datetime.date.today() + datetime.timedelta(days=1)),
        }

    def test_form_creates_experiment(self):
        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.project, self.project)
        self.assertEqual(experiment.status, experiment.STATUS_CREATED)
        self.assertEqual(experiment.name, self.data['name'])
        self.assertEqual(experiment.slug, 'a-new-experiment')
        self.assertEqual(
            experiment.short_description, self.data['short_description'])
        self.assertEqual(
            experiment.population_percent, decimal.Decimal('10.000'))
        self.assertEqual(
            experiment.firefox_version, self.data['firefox_version'])
        self.assertEqual(
            experiment.firefox_channel, self.data['firefox_channel'])
        self.assertEqual(
            experiment.client_matching, self.data['client_matching'])
        self.assertEqual(
            experiment.proposed_start_date, self.data['proposed_start_date'])
        self.assertEqual(
            experiment.proposed_end_date, self.data['proposed_end_date'])

        self.assertEqual(experiment.changes.count(), 1)
        change = experiment.changes.get()
        self.assertEqual(change.old_status, None)
        self.assertEqual(change.new_status, experiment.status)
        self.assertEqual(change.changed_by, self.request.user)

    def test_form_is_invalid_if_population_percent_is_0(self):
        self.data['population_percent'] = '0'
        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('population_percent', form.errors)

    def test_form_is_invalid_if_population_percent_below_0(self):
        self.data['population_percent'] = '-1'
        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('population_percent', form.errors)

    def test_form_is_invalid_if_population_percent_above_100(self):
        self.data['population_percent'] = '101'
        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('population_percent', form.errors)


class TestExperimentVariantsForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.data = {
            'pref_key': 'browser.testing.tests-enabled',
            'pref_type': Experiment.PREF_TYPE_BOOL,
            'pref_branch': Experiment.PREF_BRANCH_DEFAULT,
            'control-name': 'The Control Variant',
            'control-description': 'Its the control! So controlly.',
            'control-ratio': 60,
            'control-value': 'false',
            'experimental-name': 'The Experimental Variant',
            'experimental-description': (
                'Its the experimental! So experimentally.'),
            'experimental-ratio': 40,
            'experimental-value': 'true',
        }

    def test_form_saves_variants(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)

        form = ExperimentVariantsForm(
            request=self.request, data=self.data, instance=created_experiment)
        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.pref_key, self.data['pref_key'])
        self.assertEqual(experiment.pref_type, self.data['pref_type'])
        self.assertEqual(experiment.pref_branch, self.data['pref_branch'])
        self.assertEqual(experiment.control.name, self.data['control-name'])
        self.assertEqual(
            experiment.control.description, self.data['control-description'])
        self.assertEqual(experiment.control.ratio, self.data['control-ratio'])
        self.assertEqual(experiment.control.value, self.data['control-value'])
        self.assertEqual(
            experiment.variant.name, self.data['experimental-name'])
        self.assertEqual(
            experiment.variant.description,
            self.data['experimental-description'],
        )
        self.assertEqual(
            experiment.variant.ratio, self.data['experimental-ratio'])
        self.assertEqual(
            experiment.variant.value, self.data['experimental-value'])

    def test_form_is_invalid_if_control_is_invalid(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)
        self.data['control-ratio'] = 'invalid'
        form = ExperimentVariantsForm(
            request=self.request, data=self.data, instance=created_experiment)
        self.assertFalse(form.is_valid())

    def test_form_is_invalid_if_experimental_is_invalid(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)
        self.data['experimental-ratio'] = 'invalid'
        form = ExperimentVariantsForm(
            request=self.request, data=self.data, instance=created_experiment)
        self.assertFalse(form.is_valid())


class TestExperimentObjectivesForm(MockRequestMixin, TestCase):

    def test_form_saves_objectives(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)

        data = {
            'objectives': 'The objective is to experiment!',
            'analysis': 'Lets analyze the results!',
        }

        form = ExperimentObjectivesForm(
            request=self.request, data=data, instance=created_experiment)

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.objectives, data['objectives'])
        self.assertEqual(experiment.analysis, data['analysis'])


class TestExperimentRisksForm(MockRequestMixin, TestCase):

    def test_form_saves_risks(self):
        created_experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)

        data = {
            'risk_partner_related': False,
            'risk_brand': True,
            'risk_fast_shipped': False,
            'risk_confidential': True,
            'risk_release_population': False,
            'risks': 'There are some risks',
            'testing': 'Always be sure to test!',
        }

        form = ExperimentRisksForm(
            request=self.request, data=data, instance=created_experiment)

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(
            experiment.risk_partner_related, data['risk_partner_related'])
        self.assertEqual(experiment.risk_brand, data['risk_brand'])
        self.assertEqual(
            experiment.risk_fast_shipped, data['risk_fast_shipped'])
        self.assertEqual(
            experiment.risk_confidential, data['risk_confidential'])
        self.assertEqual(
            experiment.risk_release_population,
            data['risk_release_population'],
        )
        self.assertEqual(experiment.risks, data['risks'])
        self.assertEqual(experiment.testing, data['testing'])
