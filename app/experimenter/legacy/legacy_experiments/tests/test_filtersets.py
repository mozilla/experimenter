import datetime
import random
from urllib.parse import urlencode

from django.conf import settings
from django.http.request import QueryDict
from django.test import TestCase
from django.urls import reverse

from experimenter.base.tests.mixins import MockRequestMixin
from experimenter.legacy.legacy_experiments.filtersets import ExperimentFilterset
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.legacy.legacy_experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory
from experimenter.projects.tests.factories import ProjectFactory


class TestExperimentFilterset(MockRequestMixin, TestCase):
    def test_filters_by_multiple_types(self):
        pref = ExperimentFactory.create(type=Experiment.TYPE_PREF)
        addon = ExperimentFactory.create(type=Experiment.TYPE_ADDON)
        ExperimentFactory.create(type=Experiment.TYPE_GENERIC)

        filter = ExperimentFilterset(
            data=QueryDict(
                urlencode({"type": [Experiment.TYPE_PREF, Experiment.TYPE_ADDON]}, True)
            ),
            queryset=Experiment.objects.all(),
        )
        self.assertTrue(filter.is_valid())
        self.assertEqual(set(filter.qs), set([pref, addon]))
        self.assertEqual(filter.get_type_display_value(), "Pref-Flip, Add-On")

    def test_filters_by_no_project_type(self):
        project1 = ProjectFactory.create()
        exp1 = ExperimentFactory.create(projects=[])
        ExperimentFactory.create(projects=[project1])
        ExperimentFactory.create(projects=[project1])

        data = QueryDict("projects=null")

        filter = ExperimentFilterset(data=data, queryset=Experiment.objects.all())

        self.assertTrue(filter.is_valid())
        self.assertCountEqual(filter.qs, [exp1])
        display_value = filter.get_project_display_value()
        self.assertEqual("No Projects", display_value)

    def test_filters_by_multiple_project_type(self):
        project1 = ProjectFactory.create()
        project2 = ProjectFactory.create()
        project3 = ProjectFactory.create()
        exp1 = ExperimentFactory.create(projects=[project1, project2])
        exp2 = ExperimentFactory.create(projects=[project2])
        ExperimentFactory.create(projects=[project3])

        data = QueryDict(f"projects={project1.id}&projects={project2.id}")

        filter = ExperimentFilterset(data=data, queryset=Experiment.objects.all())

        self.assertTrue(filter.is_valid())
        self.assertCountEqual(filter.qs, [exp1, exp2])
        display_value = filter.get_project_display_value()
        self.assertIn(project1.name, display_value)
        self.assertIn(project2.name, display_value)

    def test_filters_out_archived_by_default(self):
        for i in range(3):
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=False)

        for i in range(3):
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=True)

        filter = ExperimentFilterset(data={}, queryset=Experiment.objects.all())

        self.assertEqual(set(filter.qs), set(Experiment.objects.filter(archived=False)))

    def test_allows_archived_if_True(self):
        for i in range(3):
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=False)

        for i in range(3):
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=True)

        filter = ExperimentFilterset(
            data={"archived": True}, queryset=Experiment.objects.all()
        )

        self.assertEqual(set(filter.qs), set(Experiment.objects.all()))

    def test_filters_by_owner(self):
        owner = UserFactory.create()

        for i in range(3):
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, owner=owner)
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        filter = ExperimentFilterset(
            {"owner": owner.id}, queryset=Experiment.objects.all()
        )

        self.assertEqual(set(filter.qs), set(Experiment.objects.filter(owner=owner)))
        self.assertEqual(filter.get_owner_display_value(), str(owner))

    def test_filters_by_status(self):
        for i in range(3):
            ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
            ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)

        filter = ExperimentFilterset(
            {"status": Experiment.STATUS_DRAFT}, queryset=Experiment.objects.all()
        )

        self.assertEqual(
            set(filter.qs), set(Experiment.objects.filter(status=Experiment.STATUS_DRAFT))
        )

    def test_filters_by_firefox_version(self):

        exp_1 = ExperimentFactory.create_with_variants(
            name="Experiment 1", firefox_min_version="58.0", firefox_max_version="62.0"
        )
        exp_2 = ExperimentFactory.create_with_variants(
            name="Experiment 2", firefox_min_version="59.0", firefox_max_version="60.0"
        )
        ExperimentFactory.create_with_variants(
            name="Experiment 4", firefox_min_version="62.0", firefox_max_version="68.0"
        )
        exp_3 = ExperimentFactory.create_with_variants(
            name="Experiment 3", firefox_min_version="59.0", firefox_max_version=""
        )
        ExperimentFactory.create_with_variants(
            name="Experiment 5", firefox_min_version="54.0", firefox_max_version="56.0"
        )

        filter = ExperimentFilterset(
            {"firefox_version": "59.0"}, queryset=Experiment.objects.all()
        )
        self.assertEqual(set(filter.qs), set([exp_1, exp_2, exp_3]))

    def test_filters_by_firefox_channel(self):
        include_channel = Experiment.CHANNEL_CHOICES[1][0]
        exclude_channel = Experiment.CHANNEL_CHOICES[2][0]

        for i in range(3):
            ExperimentFactory.create_with_variants(firefox_channel=include_channel)
            ExperimentFactory.create_with_variants(firefox_channel=exclude_channel)

        filter = ExperimentFilterset(
            {"firefox_channel": include_channel}, queryset=Experiment.objects.all()
        )
        self.assertEqual(
            set(filter.qs),
            set(Experiment.objects.filter(firefox_channel=include_channel)),
        )

    def test_list_filters_by_search_text(self):
        user_email = "user@example.com"

        exp_1 = ExperimentFactory.create_with_status(
            random.choice(Experiment.STATUS_CHOICES)[0],
            name="Experiment One Cat",
            short_description="",
            slug="exp-1",
            related_work="",
            addon_experiment_id="1",
            pref_name="",
            public_description="",
            objectives="",
            analysis="",
            engineering_owner="",
            bugzilla_id="4",
            recipe_slug="",
        )

        exp_2 = ExperimentFactory.create_with_status(
            random.choice(Experiment.STATUS_CHOICES)[0],
            name="Experiment Two Cat",
            short_description="",
            slug="exp-2",
            related_work="",
            addon_experiment_id="2",
            pref_name="",
            public_description="",
            objectives="",
            analysis="",
            engineering_owner="",
            bugzilla_id="5",
            recipe_slug="",
        )

        exp_3 = ExperimentFactory.create_with_status(
            random.choice(Experiment.STATUS_CHOICES)[0],
            name="Experiment Three Dog",
            short_description="",
            slug="exp-3",
            related_work="",
            addon_experiment_id="3",
            pref_name="",
            public_description="",
            objectives="",
            analysis="",
            engineering_owner="",
            bugzilla_id="6",
            recipe_slug="",
        )

        first_response_context = self.client.get(
            "{url}?{params}".format(
                url=reverse("home"), params=urlencode({"search": "Cat"})
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        ).context[0]

        second_response_context = self.client.get(
            "{url}?{params}".format(
                url=reverse("home"), params=urlencode({"search": "Dog"})
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        ).context[0]

        self.assertEqual(set(first_response_context["experiments"]), set([exp_1, exp_2]))
        self.assertEqual(set(second_response_context["experiments"]), set([exp_3]))

    def test_filters_by_review_in_qa(self):
        exp_1 = ExperimentFactory.create_with_variants(
            review_qa_requested=True, review_qa=False
        )
        ExperimentFactory.create_with_variants(review_qa_requested=False, review_qa=False)
        ExperimentFactory.create_with_variants(review_qa_requested=True, review_qa=True)

        filter = ExperimentFilterset({"in_qa": "on"}, queryset=Experiment.objects.all())

        self.assertEqual(set(filter.qs), set([exp_1]))

    def test_filters_experiments_with_surveys(self):
        exp_1 = ExperimentFactory.create_with_variants(survey_required=True)
        exp_2 = ExperimentFactory.create_with_variants(
            survey_required=True, review_qa=False
        )
        ExperimentFactory.create_with_variants(survey_required=False)

        filter = ExperimentFilterset({"surveys": "on"}, queryset=Experiment.objects.all())

        self.assertEqual(set(filter.qs), set([exp_1, exp_2]))

    def test_filters_for_subscribed_experiments(self):
        exp_1 = ExperimentFactory.create(name="Experiment", slug="experiment")
        ExperimentFactory.create()
        ExperimentFactory.create()

        exp_1.subscribers.add(self.user)

        subscribed_filter = ExperimentFilterset(
            {"subscribed": "on"}, request=self.request, queryset=Experiment.objects.all()
        )

        self.assertEqual(list(subscribed_filter.qs), [exp_1])

    def test_filters_for_paused_experiments(self):
        exp_1 = ExperimentFactory.create(
            name="Experiment", is_paused=True, status=Experiment.STATUS_LIVE
        )
        ExperimentFactory.create()
        ExperimentFactory.create()

        pause_filter = ExperimentFilterset(
            {"is_paused": "on"}, request=self.request, queryset=Experiment.objects.all()
        )

        self.assertEqual(list(pause_filter.qs), [exp_1])

    def test_filters_for_longrunning_experiments(self):
        exp_1 = ExperimentFactory.create(
            name="Experiment 1", firefox_min_version="67.0b", firefox_max_version="70.0b"
        )
        exp_2 = ExperimentFactory.create(
            name="Experiment 2", firefox_min_version="64.0", firefox_max_version="69.0"
        )
        ExperimentFactory.create(
            name="Experiment 3", firefox_min_version="64.0", firefox_max_version=""
        )
        ExperimentFactory.create(
            name="Experiment 4", firefox_min_version="64.0", firefox_max_version="65.0"
        )

        filter = ExperimentFilterset(
            {"longrunning": "on"}, request=self.request, queryset=Experiment.objects.all()
        )

        self.assertEqual(set(filter.qs), set([exp_1, exp_2]))

    def test_filters_for_results_completed(self):
        exp1 = ExperimentFactory.create(results_url="https://example.com")
        exp2 = ExperimentFactory.create(results_initial="some random initial blurb")
        exp3 = ExperimentFactory.create(results_lessons_learned="a lesson was learned")
        exp4 = ExperimentFactory.create(
            results_url="https://example.com",
            results_initial="some other random initial blurb",
            results_lessons_learned="a very important lesson was learned",
        )
        ExperimentFactory.create()
        ExperimentFactory.create(results_lessons_learned="")

        filter = ExperimentFilterset(
            {"completed_results": "on"},
            request=self.request,
            queryset=Experiment.objects.all(),
        )
        self.assertCountEqual(list(filter.qs), [exp1, exp2, exp3, exp4])

    def set_up_date_tests(self):

        self.exp_1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="experiment 1",
            proposed_start_date=datetime.date(2019, 4, 5),
            proposed_duration=30,
            proposed_enrollment=3,
        )

        self.exp_2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="experiment 2",
            proposed_start_date=datetime.date(2019, 3, 29),
            proposed_duration=14,
            proposed_enrollment=4,
        )

        self.exp_3 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="experiment 3",
            proposed_start_date=datetime.date(2019, 5, 29),
            proposed_duration=30,
            proposed_enrollment=None,
        )

        self.exp_4 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="experiment 4",
            proposed_start_date=datetime.date(2019, 3, 15),
            proposed_duration=25,
            proposed_enrollment=1,
        )

        self.start_range_date = "2019-04-01"
        self.end_range_date = "2019-05-01"
        self.user_email = "user@example.com"

    def test_list_shows_all_experiments_with_start_in_range(self):
        self.set_up_date_tests()

        filter = ExperimentFilterset(
            data={
                "experiment_date_field": Experiment.EXPERIMENT_STARTS,
                "date_range_after": self.start_range_date,
                "date_range_before": self.end_range_date,
            }
        )

        self.assertEqual(set(filter.qs), set([self.exp_1]))
        self.assertEqual(
            filter.get_display_start_date_info(),
            "starting between 2019-04-01 and 2019-05-01",
        )

    def test_list_shows_all_experiments_with_pause_in_range(self):
        self.set_up_date_tests()

        filter = ExperimentFilterset(
            data={
                "experiment_date_field": Experiment.EXPERIMENT_PAUSES,
                "date_range_after": self.start_range_date,
                "date_range_before": self.end_range_date,
            }
        )

        self.assertEqual(set(filter.qs), set([self.exp_1, self.exp_2]))
        self.assertEqual(
            filter.get_display_start_date_info(),
            "pausing between 2019-04-01 and 2019-05-01",
        )

    def test_list_shows_all_experiments_with_end_in_range(self):
        self.set_up_date_tests()

        filter = ExperimentFilterset(
            data={
                "experiment_date_field": Experiment.EXPERIMENT_ENDS,
                "date_range_after": self.start_range_date,
                "date_range_before": self.end_range_date,
            }
        )

        self.assertEqual(set(filter.qs), set([self.exp_2, self.exp_4]))
        self.assertEqual(
            filter.get_display_start_date_info(),
            "ending between 2019-04-01 and 2019-05-01",
        )

    def test_list_shows_all_experiments_with_start_in_range_start_date_only(self):
        self.set_up_date_tests()

        filter = ExperimentFilterset(
            data={
                "experiment_date_field": Experiment.EXPERIMENT_STARTS,
                "date_range_after": self.start_range_date,
                "date_range_before": "",
            }
        )

        self.assertEqual(set(filter.qs), set([self.exp_1, self.exp_3]))
        self.assertEqual(
            filter.get_display_start_date_info(), "starting after 2019-04-01"
        )

    def test_list_shows_all_experiments_with_start_in_range_end_date_only(self):
        self.set_up_date_tests()

        filter = ExperimentFilterset(
            data={
                "experiment_date_field": Experiment.EXPERIMENT_STARTS,
                "date_range_after": "",
                "date_range_before": self.end_range_date,
            }
        )

        self.assertEqual(set(filter.qs), set([self.exp_1, self.exp_2, self.exp_4]))
        self.assertEqual(
            filter.get_display_start_date_info(), "starting before 2019-05-01"
        )

    def test_list_shows_all_experiment_when_date_field_has_no_value(self):
        self.set_up_date_tests()

        filter = ExperimentFilterset(
            data={
                "experiment_date_field": "",
                "date_range_after": self.start_range_date,
                "date_range_before": self.end_range_date,
            }
        )

        self.assertEqual(
            set(filter.qs), set([self.exp_1, self.exp_2, self.exp_3, self.exp_4])
        )

    def test_filters_by_analysis_owner(self):
        user = UserFactory.create()
        experiment = ExperimentFactory.create(analysis_owner=user)
        filter = ExperimentFilterset(data={"analysis_owner": user.id})
        self.assertEqual(set(filter.qs), set([experiment]))

    def test_filter_by_analysis_owner_invalid_for_non_analysis_owner(self):
        user = UserFactory.create()
        filter = ExperimentFilterset(data={"analysis_owner": user.id})
        self.assertFalse(filter.is_valid())
