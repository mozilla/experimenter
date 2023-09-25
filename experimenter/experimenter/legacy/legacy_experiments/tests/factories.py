import datetime
import decimal
import json
import random

import factory
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from experimenter.base.models import Country, Locale
from experimenter.legacy.legacy_experiments.constants import ExperimentConstants
from experimenter.legacy.legacy_experiments.models import (
    Experiment,
    ExperimentChangeLog,
    ExperimentComment,
    ExperimentVariant,
    VariantPreferences,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.projects.tests.factories import ProjectFactory

faker = Faker()
NORMANDY_STATUS_CHOICES = Experiment.STATUS_CHOICES[:-1]


class ExperimentFactory(ExperimentConstants, factory.django.DjangoModelFactory):
    type = Experiment.TYPE_PREF
    owner = factory.SubFactory(UserFactory)
    analysis_owner = factory.SubFactory(UserFactory)
    engineering_owner = factory.LazyAttribute(lambda o: faker.name())
    name = factory.LazyAttribute(lambda o: faker.unique.catch_phrase())
    slug = factory.LazyAttribute(lambda o: "{}_".format(slugify(o.name)))
    archived = False
    short_description = factory.LazyAttribute(lambda o: faker.text(200))
    public_description = factory.LazyAttribute(lambda o: faker.text(200))
    data_science_issue_url = "{base}DS-12345".format(base=settings.DS_ISSUE_HOST)
    feature_bugzilla_url = "{base}show_bug.cgi?id=12345".format(
        base=settings.BUGZILLA_HOST
    )
    related_work = "See also: https://www.example.com/myproject/"
    proposed_start_date = factory.LazyAttribute(
        lambda o: (timezone.now().date() + datetime.timedelta(days=random.randint(1, 10)))
    )
    proposed_duration = factory.LazyAttribute(lambda o: random.randint(10, 60))
    proposed_enrollment = factory.LazyAttribute(
        lambda o: random.choice([None, random.randint(2, o.proposed_duration)])
        if o.proposed_duration
        else None
    )

    population_percent = factory.LazyAttribute(
        lambda o: decimal.Decimal(random.randint(1, 10) * 10)
    )
    client_matching = "Geos: US, CA, GB\n" 'Some "additional" filtering'
    design = factory.LazyAttribute(lambda o: faker.text(50))
    pref_name = factory.LazyAttribute(
        lambda o: "browser.{pref}.enabled".format(pref=faker.word())
    )
    pref_type = factory.LazyAttribute(
        lambda o: random.choice(Experiment.PREF_TYPE_CHOICES[1:])[0]
    )
    pref_branch = factory.LazyAttribute(
        lambda o: random.choice(Experiment.PREF_BRANCH_CHOICES[1:])[0]
    )
    firefox_min_version = factory.LazyAttribute(
        lambda o: random.choice(Experiment.VERSION_CHOICES[1:])[0]
    )
    firefox_max_version = factory.LazyAttribute(
        lambda o: random.choice(Experiment.VERSION_CHOICES)[0]
    )
    firefox_channel = factory.LazyAttribute(
        lambda o: random.choice(Experiment.CHANNEL_CHOICES[1:])[0]
    )
    addon_experiment_id = factory.LazyAttribute(
        lambda o: slugify(faker.unique.catch_phrase())
    )
    addon_release_url = factory.LazyAttribute(
        lambda o: "https://www.example.com/{}-release.xpi".format(o.addon_experiment_id)
    )
    objectives = factory.LazyAttribute(lambda o: faker.text(1000))
    analysis = factory.LazyAttribute(lambda o: faker.text(1000))

    risk_partner_related = False
    risk_brand = False
    risk_fast_shipped = False
    risk_confidential = False
    risk_release_population = False
    risk_revenue = False
    risk_data_category = False
    risk_external_team_impact = False
    risk_telemetry_data = False
    risk_ux = False
    risk_security = False
    risk_revision = False
    risk_technical = False
    risk_higher_risk = False

    risk_technical_description = factory.LazyAttribute(lambda o: faker.text(500))
    risks = factory.LazyAttribute(lambda o: faker.text(500))
    testing = factory.LazyAttribute(lambda o: faker.text(500))
    test_builds = factory.LazyAttribute(lambda o: faker.text(500))
    qa_status = factory.LazyAttribute(lambda o: faker.text(500))

    review_advisory = False
    review_science = False
    review_engineering = False
    review_bugzilla = False
    review_qa = False
    review_relman = False
    review_legal = False
    review_ux = False
    review_security = False
    review_vp = False
    review_data_steward = False
    review_comms = False
    review_impacted_teams = False

    bugzilla_id = "12345"
    normandy_id = None

    message_type = ExperimentConstants.MESSAGE_TYPE_CFR

    class Meta:
        model = Experiment

    @classmethod
    def create_with_variants(cls, num_variants=3, *args, **kwargs):
        experiment = cls.create(*args, **kwargs)

        for i in range(num_variants):
            if i == 0:
                ExperimentControlFactory.create(experiment=experiment)
            else:
                ExperimentVariantFactory.create(experiment=experiment)

        return experiment

    @classmethod
    def create_with_status(cls, target_status, *args, **kwargs):
        experiment = cls.create_with_variants(*args, **kwargs)

        now = timezone.now() - datetime.timedelta(days=random.randint(100, 200))

        old_status = None
        for status_value, status_label in Experiment.STATUS_CHOICES:
            experiment.status = status_value

            ExperimentChangeLogFactory.create(
                experiment=experiment,
                old_status=old_status,
                new_status=status_value,
                changed_on=now,
            )

            if status_value == Experiment.STATUS_SHIP:
                experiment.recipe_slug = experiment.generate_recipe_slug()

            if status_value == target_status:
                break

            old_status = status_value
            now += datetime.timedelta(days=random.randint(5, 20))

        # set signoffs to true
        if experiment.is_shipped:
            review_fields = experiment.get_all_required_reviews()
            for review in review_fields:
                setattr(experiment, review, True)

        experiment.save()

        return experiment

    @factory.post_generation
    def subscribers(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.subscribers.add(*extracted)

    @factory.post_generation
    def locales(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted is None and Locale.objects.exists():
            extracted = Locale.objects.all()[:3]

        if extracted:
            self.locales.add(*extracted)

    @factory.post_generation
    def countries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted is None and Country.objects.exists():
            extracted = Country.objects.all()[:3]

        if extracted:
            self.countries.add(*extracted)

    @factory.post_generation
    def projects(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted is None:
            extracted = [ProjectFactory.create() for i in range(3)]

        self.projects.add(*extracted)


class BaseExperimentVariantFactory(factory.django.DjangoModelFactory):
    description = factory.LazyAttribute(lambda o: faker.text())
    experiment = factory.SubFactory(ExperimentFactory)
    name = factory.LazyAttribute(lambda o: faker.unique.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    message_targeting = factory.LazyAttribute(lambda o: faker.unique.catch_phrase())
    message_threshold = factory.LazyAttribute(lambda o: faker.unique.catch_phrase())
    message_triggers = factory.LazyAttribute(lambda o: faker.unique.catch_phrase())

    @factory.lazy_attribute
    def addon_release_url(self):
        return "https://www.example.com/{}-release.xpi".format(slugify(self.name))

    class Meta:
        model = ExperimentVariant


class ExperimentVariantFactory(BaseExperimentVariantFactory):
    is_control = False
    ratio = 33

    @factory.lazy_attribute
    def value(self):
        value = self.is_control
        if self.experiment.pref_type == Experiment.PREF_TYPE_INT:
            value = 10
        elif self.experiment.pref_type == Experiment.PREF_TYPE_STR:
            value = slugify(faker.unique.catch_phrase())
        return json.dumps(value)


class ExperimentControlFactory(ExperimentVariantFactory):
    is_control = True


class VariantPreferencesFactory(factory.django.DjangoModelFactory):
    variant = factory.SubFactory(ExperimentVariantFactory)
    pref_name = factory.LazyAttribute(lambda o: faker.unique.catch_phrase())
    pref_type = "string"
    pref_branch = factory.LazyAttribute(
        lambda o: random.choice(Experiment.PREF_BRANCH_CHOICES[1:])[0]
    )
    pref_value = factory.LazyAttribute(lambda o: faker.word())

    class Meta:
        model = VariantPreferences


class ExperimentChangeLogFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(ExperimentFactory)
    changed_by = factory.SubFactory(UserFactory)
    old_status = factory.LazyAttribute(
        lambda o: random.choice(NORMANDY_STATUS_CHOICES)[0]
    )
    new_status = factory.LazyAttribute(
        lambda o: random.choice(
            Experiment.STATUS_TRANSITIONS[o.old_status] or [o.old_status]
        )
    )

    class Meta:
        model = ExperimentChangeLog


class ExperimentCommentFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(ExperimentFactory)
    section = factory.LazyAttribute(
        lambda o: random.choice(Experiment.SECTION_CHOICES)[0]
    )
    created_by = factory.SubFactory(UserFactory)
    text = factory.LazyAttribute(lambda o: faker.text())

    class Meta:
        model = ExperimentComment
