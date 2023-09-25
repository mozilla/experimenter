import factory
from django.utils.text import slugify
from faker import Faker

from experimenter.projects.models import Project

faker = Faker()


class ProjectFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: faker.unique.catch_phrase())
    slug = factory.LazyAttribute(lambda o: f"{slugify(o.name)}_")

    class Meta:
        model = Project
        django_get_or_create = ("slug",)
