import datetime
import decimal
import json
import random

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.openidc.tests.factories import UserFactory
from experimenter.experiments.models import (
    Experiment,
    ExperimentChangeLog,
    ExperimentComment,
    ExperimentVariant,
)
from experimenter.projects.tests.factories import ProjectFactory

faker = FakerFactory.create()


class ExperimentFactory(factory.django.DjangoModelFactory):
    type = Experiment.TYPE_PREF
    owner = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    archived = False
    short_description = factory.LazyAttribute(
        lambda o: faker.text(random.randint(100, 500))
    )
    proposed_start_date = factory.LazyAttribute(
        lambda o: (
            datetime.date.today()
            + datetime.timedelta(days=random.randint(1, 10))
        )
    )
    proposed_end_date = factory.LazyAttribute(
        lambda o: (
            o.proposed_start_date
            + datetime.timedelta(days=random.randint(1, 10))
        )
    )
    pref_key = factory.LazyAttribute(
        lambda o: "browser.{pref}.enabled".format(
            pref=faker.catch_phrase().replace(" ", ".").lower()
        )
    )
    pref_type = factory.LazyAttribute(
        lambda o: random.choice(Experiment.PREF_TYPE_CHOICES[1:])[0]
    )
    pref_branch = factory.LazyAttribute(
        lambda o: random.choice(Experiment.PREF_BRANCH_CHOICES[1:])[0]
    )
    firefox_version = factory.LazyAttribute(
        lambda o: random.choice(Experiment.VERSION_CHOICES[1:])[0]
    )
    firefox_channel = factory.LazyAttribute(
        lambda o: random.choice(Experiment.CHANNEL_CHOICES[1:])[0]
    )
    objectives = factory.LazyAttribute(
        lambda o: faker.text(random.randint(500, 5000))
    )
    analysis_owner = factory.LazyAttribute(lambda o: faker.name())
    analysis = factory.LazyAttribute(
        lambda o: faker.text(random.randint(500, 5000))
    )
    testing = factory.LazyAttribute(
        lambda o: faker.text(random.randint(500, 5000))
    )
    risks = factory.LazyAttribute(
        lambda o: faker.text(random.randint(500, 5000))
    )
    total_users = factory.LazyAttribute(
        lambda o: random.randint(100000, 1000000)
    )
    risk_partner_related = False
    risk_brand = False
    risk_fast_shipped = False
    risk_confidential = False
    risk_release_population = False
    enrollment_dashboard_url = "http://www.example.com/enrollment"
    dashboard_url = "http://www.example.com/dashboard"
    dashboard_image_url = "http://www.example.com/dashboard.png"
    population_percent = factory.LazyAttribute(
        lambda o: decimal.Decimal(random.randint(1, 10) * 10)
    )
    client_matching = (
        "Locales: en-US, en-CA, en-GB\nGeos: US, CA, GB\n"
        'Some "additional" filtering'
    )
    review_phd = False
    review_science = False
    review_peer = False
    review_relman = False
    review_qa = False
    review_legal = False
    review_ux = False
    review_security = False

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

        now = datetime.datetime.now() - datetime.timedelta(
            days=random.randint(100, 200)
        )

        old_status = None
        for status_value, status_label in Experiment.STATUS_CHOICES:
            experiment.status = status_value
            experiment.save()

            change = ExperimentChangeLogFactory.create(
                experiment=experiment,
                old_status=old_status,
                new_status=status_value,
            )
            change.changed_on = now
            change.save()

            if status_value == target_status:
                break

            old_status = status_value
            now += datetime.timedelta(days=random.randint(5, 20))

        return experiment


class BaseExperimentVariantFactory(factory.django.DjangoModelFactory):
    description = factory.LazyAttribute(lambda o: faker.text())
    experiment = factory.SubFactory(ExperimentFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))

    class Meta:
        model = ExperimentVariant


class ExperimentVariantFactory(BaseExperimentVariantFactory):
    is_control = False
    ratio = factory.LazyAttribute(lambda o: random.randint(1, 10))

    @factory.lazy_attribute
    def value(self):
        value = self.is_control
        if self.experiment.pref_type == Experiment.PREF_TYPE_INT:
            value = random.randint(1, 100)
        elif self.experiment.pref_type == Experiment.PREF_TYPE_STR:
            value = slugify(faker.catch_phrase())
        return json.dumps(value)


class ExperimentControlFactory(ExperimentVariantFactory):
    is_control = True


class ExperimentChangeLogFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(ExperimentFactory)
    changed_by = factory.SubFactory(UserFactory)
    old_status = factory.LazyAttribute(
        lambda o: random.choice(Experiment.STATUS_CHOICES)[0]
    )
    new_status = factory.LazyAttribute(
        lambda o: random.choice(
            Experiment.STATUS_TRANSITIONS[o.old_status] or [o.old_status]
        )
    )
    message = factory.LazyAttribute(lambda o: faker.text())

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
