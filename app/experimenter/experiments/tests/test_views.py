import datetime
import decimal
import json
import random

import mock
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.models import Experiment
from experimenter.experiments.serializers import ExperimentSerializer
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.views import (
    ExperimentFormMixin,
    ExperimentCreateView,
)
from experimenter.projects.tests.factories import ProjectFactory


class TestExperimentFormMixin(TestCase):

    def test_get_form_kwargs_adds_request(self):
        class BaseTestView(object):

            def __init__(self, request):
                self.request = request

            def get_form_kwargs(self):
                return {}

        class TestView(ExperimentFormMixin, BaseTestView):
            pass

        request = mock.Mock()
        view = TestView(request=request)
        form_kwargs = view.get_form_kwargs()
        self.assertEqual(form_kwargs['request'], request)

    @mock.patch('experimenter.experiments.views.reverse')
    def test_get_success_url_returns_next_url_if_action_is_continue(
            self, mock_reverse):
        class BaseTestView(object):

            def __init__(self, request, instance):
                self.request = request
                self.object = instance

        class TestView(ExperimentFormMixin, BaseTestView):
            next_view_name = 'next-test-view'

        def mock_reverser(url_name, *args, **kwargs):
            return url_name

        mock_reverse.side_effect = mock_reverser

        instance = mock.Mock()
        instance.slug = 'slug'

        request = mock.Mock()
        request.POST = {'action': 'continue'}

        view = TestView(request, instance)
        redirect = view.get_success_url()
        self.assertEqual(redirect, TestView.next_view_name)
        mock_reverse.assert_called_with(
            TestView.next_view_name, kwargs={'slug': instance.slug})

    @mock.patch('experimenter.experiments.views.reverse')
    def test_get_success_url_returns_detail_url_if_action_is_empty(
            self, mock_reverse):
        class BaseTestView(object):

            def __init__(self, request, instance):
                self.request = request
                self.object = instance

        class TestView(ExperimentFormMixin, BaseTestView):
            next_view_name = 'next-test-view'

        def mock_reverser(url_name, *args, **kwargs):
            return url_name

        mock_reverse.side_effect = mock_reverser

        instance = mock.Mock()
        instance.slug = 'slug'

        request = mock.Mock()
        request.POST = {}

        view = TestView(request, instance)
        redirect = view.get_success_url()
        self.assertEqual(redirect, 'experiments-detail')
        mock_reverse.assert_called_with(
            'experiments-detail', kwargs={'slug': instance.slug})


class TestExperimentCreateView(TestCase):

    def test_view_creates_experiment(self):
        user_email = 'user@example.com'
        project = ProjectFactory.create()

        data = {
            'project': project.id,
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

        response = self.client.post(
            reverse('experiments-create'),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()
        self.assertEqual(experiment.status, experiment.STATUS_CREATED)
        self.assertEqual(experiment.project, project)
        self.assertEqual(experiment.name, data['name'])

        self.assertEqual(experiment.changes.count(), 1)

        change = experiment.changes.get()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, None)
        self.assertEqual(change.new_status, experiment.STATUS_CREATED)

    def test_view_finds_project_id_in_get_args(self):
        project = ProjectFactory.create()

        request = mock.Mock()
        request.GET = {'project': project.id}

        view = ExperimentCreateView(request=request)
        initial = view.get_initial()

        self.assertEqual(initial['project'], project.id)


class TestExperimentOverviewUpdateView(TestCase):

    def test_view_saves_experiment(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)

        new_start_date = (
            datetime.date.today() +
            datetime.timedelta(days=random.randint(1, 100))
        )
        new_end_date = (
            new_start_date +
            datetime.timedelta(days=random.randint(1, 100))
        )

        data = {
            'name': 'A new name!',
            'short_description': 'A new description!',
            'population_percent': '11',
            'firefox_version': Experiment.VERSION_CHOICES[-1][0],
            'firefox_channel': Experiment.CHANNEL_NIGHTLY,
            'client_matching': 'New matching!',
            'proposed_start_date': new_start_date,
            'proposed_end_date': new_end_date,
        }

        response = self.client.post(
            reverse(
                'experiments-overview-update',
                kwargs={'slug': experiment.slug},
            ),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()
        self.assertEqual(experiment.name, data['name'])
        self.assertEqual(
            experiment.short_description, data['short_description'])
        self.assertEqual(
            experiment.population_percent,
            decimal.Decimal(data['population_percent']),
        )
        self.assertEqual(experiment.firefox_version, data['firefox_version'])
        self.assertEqual(experiment.firefox_channel, data['firefox_channel'])
        self.assertEqual(experiment.proposed_start_date, new_start_date)
        self.assertEqual(experiment.proposed_end_date, new_end_date)

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, experiment.STATUS_CREATED)
        self.assertEqual(change.new_status, experiment.STATUS_CREATED)


class TestExperimentVariantsUpdateView(TestCase):

    def test_view_saves_experiment(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)

        data = {
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

        response = self.client.post(
            reverse(
                'experiments-variants-update',
                kwargs={'slug': experiment.slug},
            ),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()

        self.assertEqual(experiment.pref_key, data['pref_key'])
        self.assertEqual(experiment.pref_type, data['pref_type'])
        self.assertEqual(experiment.pref_branch, data['pref_branch'])
        self.assertEqual(experiment.control.name, data['control-name'])
        self.assertEqual(
            experiment.control.description, data['control-description'])
        self.assertEqual(experiment.control.ratio, data['control-ratio'])
        self.assertEqual(experiment.control.value, data['control-value'])
        self.assertEqual(
            experiment.variant.name, data['experimental-name'])
        self.assertEqual(
            experiment.variant.description,
            data['experimental-description'],
        )
        self.assertEqual(
            experiment.variant.ratio, data['experimental-ratio'])
        self.assertEqual(
            experiment.variant.value, data['experimental-value'])

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, experiment.STATUS_CREATED)
        self.assertEqual(change.new_status, experiment.STATUS_CREATED)


class TestExperimentObjectivesUpdateView(TestCase):

    def test_view_saves_experiment(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)

        data = {
            'objectives': 'Some new objectives!',
            'analysis': 'Some new analysis!',
        }

        response = self.client.post(
            reverse(
                'experiments-objectives-update',
                kwargs={'slug': experiment.slug},
            ),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()
        self.assertEqual(experiment.objectives, data['objectives'])
        self.assertEqual(experiment.analysis, data['analysis'])

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, experiment.STATUS_CREATED)
        self.assertEqual(change.new_status, experiment.STATUS_CREATED)


class TestExperimentRisksUpdateView(TestCase):

    def test_view_saves_experiment(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
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

        response = self.client.post(
            reverse(
                'experiments-risks-update',
                kwargs={'slug': experiment.slug},
            ),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()

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

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, experiment.STATUS_CREATED)
        self.assertEqual(change.new_status, experiment.STATUS_CREATED)


class TestExperimentDetailView(TestCase):

    def test_view_renders_correctly(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_CREATED)

        response = self.client.get(
            reverse('experiments-detail', kwargs={'slug': experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)


class TestExperimentListView(TestCase):

    def test_list_view_serializes_experiments(self):
        experiments = []

        for i in range(3):
            experiment = ExperimentFactory.create_with_variants()
            experiments.append(experiment)

        response = self.client.get(reverse('experiments-list'))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            Experiment.objects.all(), many=True).data

        self.assertEqual(serialized_experiments, json_data)

    def test_list_view_filters_by_project_slug(self):
        project = ProjectFactory.create()
        project_experiments = []

        # another projects experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants()

        # started project experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants(
                project=project)
            project_experiments.append(experiment)

        response = self.client.get(
            reverse('experiments-list'), {'project__slug': project.slug})
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            project.experiments.all(), many=True).data

        self.assertEqual(serialized_experiments, json_data)

    def test_list_view_filters_by_status(self):
        pending_experiments = []

        # new experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants()

        # pending experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants()
            experiment.status = experiment.STATUS_PENDING
            experiment.save()
            pending_experiments.append(experiment)

        response = self.client.get(
            reverse('experiments-list'),
            {'status': Experiment.STATUS_PENDING},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            Experiment.objects.filter(
                status=Experiment.STATUS_PENDING), many=True).data

        self.assertEqual(serialized_experiments, json_data)


class TestExperimentAcceptView(TestCase):

    def test_post_to_accept_view_sets_status_accepted(self):
        user_email = 'user@example.com'

        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()

        response = self.client.patch(
            reverse('experiments-accept', kwargs={'slug': experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = Experiment.objects.get(pk=experiment.pk)
        self.assertEqual(experiment.status, experiment.STATUS_ACCEPTED)

        change = experiment.changes.get()
        self.assertEqual(change.old_status, experiment.STATUS_PENDING)
        self.assertEqual(change.new_status, experiment.STATUS_ACCEPTED)
        self.assertEqual(change.changed_by.email, user_email)

    def test_post_to_accept_raises_404_for_non_pending_experiment(self):
        experiment = ExperimentFactory.create_with_variants()

        response = self.client.patch(
            reverse('experiments-accept', kwargs={'slug': experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: 'user@example.com'},
        )

        self.assertEqual(response.status_code, 404)


class TestExperimentRejectView(TestCase):

    def test_post_to_reject_view_sets_status_rejected(self):
        user_email = 'user@example.com'
        rejection_message = 'This experiment was rejected for reasons.'

        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()

        response = self.client.patch(
            reverse('experiments-reject', kwargs={'slug': experiment.slug}),
            data=json.dumps({'message': rejection_message}),
            content_type='application/json',
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = Experiment.objects.get(pk=experiment.pk)
        self.assertEqual(experiment.status, experiment.STATUS_REJECTED)

        change = experiment.changes.get()
        self.assertEqual(change.old_status, experiment.STATUS_PENDING)
        self.assertEqual(change.new_status, experiment.STATUS_REJECTED)
        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.message, rejection_message)

    def test_post_to_reject_raises_404_for_non_pending_experiment(self):
        experiment = ExperimentFactory.create_with_variants()

        response = self.client.patch(
            reverse('experiments-reject', kwargs={'slug': experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: 'user@example.com'},
        )

        self.assertEqual(response.status_code, 404)
