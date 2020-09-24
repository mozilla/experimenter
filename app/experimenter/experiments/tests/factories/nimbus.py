import decimal
import random

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusExperiment,
    NimbusIsolationGroup,
)
from experimenter.openidc.tests.factories import UserFactory

faker = FakerFactory.create()


class NimbusExperimentFactory(factory.django.DjangoModelFactory):
    owner = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusConstants.MAX_SLUG_LEN]
    )
    public_description = factory.LazyAttribute(lambda o: faker.text(200))
    proposed_duration = factory.LazyAttribute(lambda o: random.randint(10, 60))
    proposed_enrollment = factory.LazyAttribute(
        lambda o: random.choice([None, random.randint(2, o.proposed_duration)])
        if o.proposed_duration
        else None
    )
    population_percent = factory.LazyAttribute(
        lambda o: decimal.Decimal(random.randint(1, 10) * 10)
    )
    firefox_min_version = factory.LazyAttribute(
        lambda o: random.choice(NimbusExperiment.Version.choices)[0]
    )
    firefox_channel = factory.LazyAttribute(
        lambda o: random.choice(NimbusExperiment.Channel.choices)[0]
    )
    hypothesis = factory.LazyAttribute(lambda o: faker.text(1000))

    class Meta:
        model = NimbusExperiment

    @classmethod
    def create_with_status(cls, target_status, **kwargs):
        experiment = cls.create(**kwargs)

        NimbusBranchFactory.create(experiment=experiment)
        experiment.control_branch = NimbusBranchFactory.create(experiment=experiment)
        experiment.save()

        for status, _ in NimbusExperiment.Status.choices:
            if status == NimbusExperiment.Status.REVIEW.value:
                NimbusIsolationGroup.request_isolation_group_buckets(
                    experiment.slug,
                    experiment,
                    100,
                )

            if status == target_status:
                break

        return NimbusExperiment.objects.get(id=experiment.id)


class NimbusBranchFactory(factory.django.DjangoModelFactory):
    ratio = 1
    experiment = factory.SubFactory(NimbusExperimentFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusConstants.MAX_SLUG_LEN]
    )
    description = factory.LazyAttribute(lambda o: faker.text())

    class Meta:
        model = NimbusBranch


class NimbusIsolationGroupFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: slugify(faker.catch_phrase()))
    instance = factory.Sequence(lambda n: n)

    class Meta:
        model = NimbusIsolationGroup


class NimbusBucketRangeFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(NimbusExperimentFactory)
    isolation_group = factory.SubFactory(NimbusIsolationGroupFactory)
    start = factory.Sequence(lambda n: n * 100)
    count = 100

    class Meta:
        model = NimbusBucketRange
