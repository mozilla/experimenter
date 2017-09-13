import decimal
import json
import random

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.experiments.models import Experiment, ExperimentVariant
from experimenter.projects.tests.factories import ProjectFactory

faker = FakerFactory.create()


class ExperimentFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory(ProjectFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    pref_key = factory.LazyAttribute(
        lambda o: 'browser.{pref}.enabled'.format(
            pref=faker.catch_phrase().replace(' ', '.').lower()))
    pref_type = factory.LazyAttribute(
        lambda o: random.choice(Experiment.PREF_TYPE_CHOICES)[0])
    pref_branch = factory.LazyAttribute(
        lambda o: random.choice(Experiment.PREF_BRANCH_CHOICES)[0])
    firefox_version = '57.0'
    firefox_channel = factory.LazyAttribute(
        lambda o: random.choice(Experiment.CHANNEL_CHOICES)[0])
    objectives = factory.LazyAttribute(lambda o: faker.text())
    analysis = factory.LazyAttribute(lambda o: faker.text())
    dashboard_url = 'http://www.example.com/dashboard'
    dashboard_image_url = 'http://www.example.com/dashboard.png'
    population_percent = factory.LazyAttribute(
        lambda o: decimal.Decimal(random.randint(1, 10) * 10))
    client_matching = (
        'Locales: en-US, en-CA, en-GB\nGeos: US, CA, GB\n'
        'Some "additional" filtering'
    )

    class Meta:
        model = Experiment

    @classmethod
    def create_with_variants(cls, *args, **kwargs):
        experiment = cls.create(*args, **kwargs)
        ExperimentControlFactory.create(experiment=experiment)
        ExperimentVariantFactory.create(experiment=experiment)
        return experiment


class BaseExperimentVariantFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(ExperimentFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.LazyAttribute(lambda o: faker.text())

    class Meta:
        model = ExperimentVariant


class ExperimentVariantFactory(BaseExperimentVariantFactory):
    is_control = False
    ratio = factory.LazyAttribute(lambda o: random.randint(1, 10))

    @factory.lazy_attribute
    def value(self):
        if self.experiment.pref_type == Experiment.PREF_TYPE_BOOL:
            return self.is_control
        elif self.experiment.pref_type == Experiment.PREF_TYPE_INT:
            return random.randint(1, 100)
        elif self.experiment.pref_type == Experiment.PREF_TYPE_STR:
            return json.dumps(slugify(faker.catch_phrase()))


class ExperimentControlFactory(ExperimentVariantFactory):
    is_control = True
