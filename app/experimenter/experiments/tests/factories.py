import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.projects.tests.factories import ProjectFactory
from experimenter.experiments.models import Experiment, ExperimentVariant

faker = FakerFactory.create()


class ExperimentFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory(ProjectFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    pref_key = 'experiment'
    objectives = factory.LazyAttribute(lambda o: faker.paragraphs())
    analysis = factory.LazyAttribute(lambda o: faker.paragraphs())
    dashboard_url = 'http://www.example.com/dashboard'
    dashboard_image_url = 'http://www.example.com/dashboard.png'

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
    description = factory.LazyAttribute(lambda o: faker.paragraphs())

    class Meta:
        model = ExperimentVariant


class ExperimentControlFactory(BaseExperimentVariantFactory):
    is_control = True
    ratio = 1
    value = 'false'


class ExperimentVariantFactory(BaseExperimentVariantFactory):
    is_control = False
    ratio = 1
    value = 'true'
