import datetime
import decimal
import random
from urllib.parse import urlencode

import mock
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory
from experimenter.experiments.views import (
    ExperimentCreateView,
    ExperimentFilterset,
    ExperimentFormMixin,
    ExperimentOrderingForm,
)
from experimenter.projects.tests.factories import ProjectFactory


class TestExperimentFilterset(TestCase):

    def test_filters_out_archived_by_default(self):
        for i in range(3):
            ExperimentFactory.create_with_status(
                Experiment.STATUS_DRAFT, archived=False)

        for i in range(3):
            ExperimentFactory.create_with_status(
                Experiment.STATUS_DRAFT, archived=True)

        filter = ExperimentFilterset(
            data={},
            queryset=Experiment.objects.all(),
        )

        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.filter(archived=False)),
        )

    def test_allows_archived_if_True(self):
        for i in range(3):
            ExperimentFactory.create_with_status(
                Experiment.STATUS_DRAFT, archived=False)

        for i in range(3):
            ExperimentFactory.create_with_status(
                Experiment.STATUS_DRAFT, archived=True)

        filter = ExperimentFilterset(
            data={'archived': True},
            queryset=Experiment.objects.all(),
        )

        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.all()),
        )

    def test_filters_by_project(self):
        project = ProjectFactory.create()

        for i in range(3):
            ExperimentFactory.create_with_status(
                Experiment.STATUS_DRAFT, project=project)
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        filter = ExperimentFilterset(
            {'project': project.id},
            queryset=Experiment.objects.all(),
        )

        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.filter(project=project)),
        )

    def test_filters_by_owner(self):
        owner = UserFactory.create()

        for i in range(3):
            ExperimentFactory.create_with_status(
                Experiment.STATUS_DRAFT, owner=owner)
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        filter = ExperimentFilterset(
            {'owner': owner.id},
            queryset=Experiment.objects.all(),
        )

        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.filter(owner=owner)),
        )

    def test_filters_by_status(self):
        for i in range(3):
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
            ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)

        filter = ExperimentFilterset(
            {'status': Experiment.STATUS_DRAFT},
            queryset=Experiment.objects.all(),
        )

        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.filter(status=Experiment.STATUS_DRAFT)),
        )

    def test_filters_by_firefox_version(self):
        include_version = Experiment.VERSION_CHOICES[1][0]
        exclude_version = Experiment.VERSION_CHOICES[2][0]

        for i in range(3):
            ExperimentFactory.create_with_variants(
                firefox_version=include_version)
            ExperimentFactory.create_with_variants(
                firefox_version=exclude_version)

        filter = ExperimentFilterset(
            {'firefox_version': include_version},
            queryset=Experiment.objects.all(),
        )
        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.filter(firefox_version=include_version)),
        )

    def test_filters_by_firefox_channel(self):
        include_channel = Experiment.CHANNEL_CHOICES[1][0]
        exclude_channel = Experiment.CHANNEL_CHOICES[2][0]

        for i in range(3):
            ExperimentFactory.create_with_variants(
                firefox_channel=include_channel)
            ExperimentFactory.create_with_variants(
                firefox_channel=exclude_channel)

        filter = ExperimentFilterset(
            {'firefox_channel': include_channel},
            queryset=Experiment.objects.all(),
        )
        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.filter(firefox_channel=include_channel)),
        )


class TestExperimengOrderingForm(TestCase):

    def test_accepts_valid_ordering(self):
        ordering = ExperimentOrderingForm.ORDERING_CHOICES[1][0]
        form = ExperimentOrderingForm({'ordering': ordering})
        self.assertTrue(form.is_valid())

    def test_rejects_invalid_ordering(self):
        form = ExperimentOrderingForm({'ordering': 'invalid ordering'})
        self.assertFalse(form.is_valid())


class TestExperimentListView(TestCase):

    def test_list_view_lists_experiments_with_default_order_no_archived(self):
        user_email = 'user@example.com'

        # Archived experiment is ommitted
        ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, archived=True)

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0])

        experiments = Experiment.objects.all().filter(archived=False).order_by(
            ExperimentOrderingForm.ORDERING_CHOICES[0][0])

        response = self.client.get(
            reverse('home'),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(context['experiments']), list(experiments))

    def test_list_view_shows_all_including_archived(self):
        user_email = 'user@example.com'

        # Archived experiment is included
        ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, archived=True)

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0])

        experiments = Experiment.objects.all()

        response = self.client.get(
            '{url}?{params}'.format(
                url=reverse('home'),
                params=urlencode({
                    'archived': True,
                }),
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(context['experiments']), set(experiments))

    def test_list_view_filters_and_orders_experiments(self):
        user_email = 'user@example.com'

        ordering = 'latest_change'
        filtered_channel = Experiment.CHANNEL_CHOICES[1][0]
        filtered_owner = UserFactory.create()
        filtered_project = ProjectFactory.create()
        filtered_status = Experiment.STATUS_DRAFT
        filtered_version = Experiment.VERSION_CHOICES[1][0]

        for i in range(10):
            ExperimentFactory.create_with_status(
                firefox_channel=filtered_channel,
                firefox_version=filtered_version,
                owner=filtered_owner,
                project=filtered_project,
                target_status=filtered_status,
            )

        for i in range(10):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0])

        filtered_ordered_experiments = Experiment.objects.filter(
            firefox_channel=filtered_channel,
            firefox_version=filtered_version,
            owner=filtered_owner,
            project=filtered_project,
            status=filtered_status,
        ).order_by(ordering)

        response = self.client.get(
            '{url}?{params}'.format(
                url=reverse('home'),
                params=urlencode({
                    'firefox_channel': filtered_channel,
                    'firefox_version': filtered_version,
                    'ordering': ordering,
                    'owner': filtered_owner.id,
                    'project': filtered_project.id,
                    'status': filtered_status,
                }),
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(context['experiments']),
            list(filtered_ordered_experiments),
        )


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
        self.assertEqual(experiment.status, experiment.STATUS_DRAFT)
        self.assertEqual(experiment.project, project)
        self.assertEqual(experiment.name, data['name'])

        self.assertEqual(experiment.changes.count(), 1)

        change = experiment.changes.get()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, None)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)

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
            Experiment.STATUS_DRAFT)

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
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestExperimentVariantsUpdateView(TestCase):

    def test_view_saves_experiment(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT)

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
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestExperimentObjectivesUpdateView(TestCase):

    def test_view_saves_experiment(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT)

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
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestExperimentRisksUpdateView(TestCase):

    def test_view_saves_experiment(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT)

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
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestExperimentDetailView(TestCase):

    def test_view_renders_correctly(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT)

        response = self.client.get(
            reverse('experiments-detail', kwargs={'slug': experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)


class TestExperimentStatusUpdateView(TestCase):

    def test_view_updates_status_and_redirects(self):
        user_email = 'user@example.com'
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT)

        new_status = experiment.STATUS_REVIEW

        response = self.client.post(
            reverse(
                'experiments-status-update', kwargs={'slug': experiment.slug}),
            {'status': new_status},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertRedirects(
            response,
            reverse('experiments-detail', kwargs={'slug': experiment.slug}),
            fetch_redirect_response=False,
        )
        updated_experiment = Experiment.objects.get(slug=experiment.slug)
        self.assertEqual(updated_experiment.status, new_status)

    def test_view_redirects_on_failure(self):
        user_email = 'user@example.com'
        original_status = Experiment.STATUS_DRAFT
        experiment = ExperimentFactory.create_with_status(
            original_status)

        response = self.client.post(
            reverse(
                'experiments-status-update', kwargs={'slug': experiment.slug}),
            {'status': Experiment.STATUS_COMPLETE},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertRedirects(
            response,
            reverse('experiments-detail', kwargs={'slug': experiment.slug}),
            fetch_redirect_response=False,
        )
        updated_experiment = Experiment.objects.get(slug=experiment.slug)
        self.assertEqual(updated_experiment.status, original_status)
