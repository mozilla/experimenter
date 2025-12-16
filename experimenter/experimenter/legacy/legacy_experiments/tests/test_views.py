import random
import re
from urllib.parse import urlencode

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.legacy.legacy_experiments.forms import ExperimentOrderingForm
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.legacy.legacy_experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestExperimentListView(TestCase):
    def test_list_view_lists_experiments_with_default_order_no_archived(self):
        user_email = "user@example.com"

        # Archived experiment is ommitted
        ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=True)

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        experiments = (
            Experiment.objects.all()
            .filter(archived=False)
            .order_by(ExperimentOrderingForm.ORDERING_CHOICES[0][0])
        )

        response = self.client.get(
            reverse("home"), **{settings.OPENIDC_EMAIL_HEADER: user_email}
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(context["experiments"]), list(experiments))

    def test_list_view_shows_all_including_archived(self):
        user_email = "user@example.com"

        # Archived experiment is included
        ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=True)

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        experiments = Experiment.objects.all()

        response = self.client.get(
            "{url}?{params}".format(
                url=reverse("home"), params=urlencode({"archived": True})
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(context["experiments"]), set(experiments))

    def test_list_view_filters_and_orders_experiments(self):
        user_email = "user@example.com"

        ordering = "latest_change"
        filtered_channel = Experiment.CHANNEL_CHOICES[1][0]
        filtered_owner = UserFactory.create()
        filtered_status = Experiment.STATUS_DRAFT
        filtered_types = (Experiment.TYPE_PREF, Experiment.TYPE_GENERIC)
        filtered_version = Experiment.VERSION_CHOICES[1][0]

        for i in range(3):
            for filtered_type in filtered_types:
                ExperimentFactory.create_with_status(
                    firefox_channel=filtered_channel,
                    firefox_min_version=filtered_version,
                    owner=filtered_owner,
                    target_status=filtered_status,
                    type=filtered_type,
                )

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        filtered_ordered_experiments = Experiment.objects.filter(
            firefox_channel=filtered_channel,
            firefox_min_version=filtered_version,
            owner=filtered_owner,
            status=filtered_status,
            type__in=filtered_types,
        ).order_by(ordering)

        response = self.client.get(
            "{url}?{params}".format(
                url=reverse("home"),
                params=urlencode(
                    {
                        "firefox_channel": filtered_channel,
                        "firefox_version": filtered_version,
                        "ordering": ordering,
                        "owner": filtered_owner.id,
                        "status": filtered_status,
                        "type": filtered_types,
                    },
                    True,
                ),
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(context["experiments"]), list(filtered_ordered_experiments))

    def test_list_view_total_experiments_count(self):
        user_email = "user@example.com"

        number_of_experiments = settings.EXPERIMENTS_PAGINATE_BY + 1
        for i in range(number_of_experiments):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        response = self.client.get(
            reverse("home"), **{settings.OPENIDC_EMAIL_HEADER: user_email}
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        total_count_regex = re.compile(rf"{number_of_experiments}\s+Deliveries")
        self.assertTrue(total_count_regex.search(html))

        # Go to page 2, and the total shouldn't change.
        response = self.client.get(
            "{url}?{params}".format(url=reverse("home"), params=urlencode({"page": 2})),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertTrue(total_count_regex.search(html))
        self.assertTrue("Page 2" in html)


class TestExperimentDetailView(TestCase):
    def test_view_renders_correctly(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        response = self.client.get(
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experiments/detail_draft.html")
        self.assertTemplateUsed(response, "experiments/detail_base.html")

    def test_view_renders_locales_correctly(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        experiment.locales.add(LocaleFactory(code="yy", name="Why"))
        experiment.locales.add(LocaleFactory(code="xx", name="Xess"))
        response = self.client.get(
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

    def test_view_renders_countries_correctly(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        experiment.countries.add(CountryFactory(code="YY", name="Wazoo"))
        experiment.countries.add(CountryFactory(code="XX", name="Xanadu"))
        response = self.client.get(
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)


class TestNimbusUIView(TestCase):
    def test_page_loads(self):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("nimbus-list"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)


class Test404View(TestCase):
    def test_404(self):
        user_email = "user@example.com"
        response = self.client.get(
            # test path should be a string that doesn't match any existing url patterns
            # or django will attempt to 301 and append a slash before 404ing
            "/invalid/",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertTemplateUsed(response, "404.html")
        self.assertEqual(response.status_code, 404)
