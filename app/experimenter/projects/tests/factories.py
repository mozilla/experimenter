import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.projects.models import Project

faker = FakerFactory.create()


class ProjectFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: slugify(o.name))

    class Meta:
        model = Project
