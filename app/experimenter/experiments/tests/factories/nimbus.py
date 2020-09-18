import random

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.experiments.models import NimbusExperiment
from experimenter.openidc.tests.factories import UserFactory

faker = FakerFactory.create()


class NimbusExperimentFactory(factory.django.DjangoModelFactory):
    owner = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(lambda o: "{}_".format(slugify(o.name)))
    public_description = factory.LazyAttribute(lambda o: faker.text(200))
    proposed_duration = factory.LazyAttribute(lambda o: random.randint(10, 60))
    proposed_enrollment = factory.LazyAttribute(
        lambda o: random.choice([None, random.randint(2, o.proposed_duration)])
        if o.proposed_duration
        else None
    )

    firefox_min_version = factory.LazyAttribute(
        lambda o: random.choice(NimbusExperiment.VERSION_CHOICES[1:])[0]
    )
    firefox_max_version = factory.LazyAttribute(
        lambda o: random.choice(NimbusExperiment.VERSION_CHOICES)[0]
    )
    firefox_channel = factory.LazyAttribute(
        lambda o: random.choice(NimbusExperiment.CHANNEL_CHOICES[1:])[0]
    )
    objectives = factory.LazyAttribute(lambda o: faker.text(1000))

    bugzilla_id = "12345"

    class Meta:
        model = NimbusExperiment
