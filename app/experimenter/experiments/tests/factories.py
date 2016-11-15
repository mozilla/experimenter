import datetime

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.projects.tests.factories import ProjectFactory
from experimenter.experiments.models import Experiment, ExperimentVariant

faker = FakerFactory.create()


class ExperimentFactory(factory.django.DjangoModelFactory):
    active = True
    project = factory.SubFactory(ProjectFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    objectives = factory.LazyAttribute(lambda o: faker.paragraphs())
    success_criteria = factory.LazyAttribute(lambda o: faker.paragraphs())
    start_date = factory.LazyAttribute(lambda o: datetime.datetime.now())
    end_date = factory.LazyAttribute(
        lambda o: o.start_date + datetime.timedelta(weeks=2))

    class Meta:
        model = Experiment

    @classmethod
    def create_with_variants(cls, *args, **kwargs):
        experiment = cls.create(*args, **kwargs)
        ControlVariantFactory.create(experiment=experiment)
        ExperimentVariantFactory.create(experiment=experiment)
        return experiment


class BaseExperimentVariantFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(ExperimentFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.LazyAttribute(lambda o: faker.paragraphs())

    class Meta:
        model = ExperimentVariant


class ControlVariantFactory(BaseExperimentVariantFactory):
    is_control = True
    threshold = 0
    value = 'false'


class ExperimentVariantFactory(BaseExperimentVariantFactory):
    is_control = False
    threshold = 10
    value = 'true'
