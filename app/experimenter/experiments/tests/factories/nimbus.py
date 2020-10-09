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
    NimbusFeatureConfig,
    NimbusIsolationGroup,
    NimbusProbe,
    NimbusProbeSet,
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
    application = factory.LazyAttribute(
        lambda o: random.choice(NimbusExperiment.Application.choices)[0]
    )
    channels = factory.LazyAttribute(
        lambda o: NimbusExperiment.ApplicationChannels.get(o.application, []),
    )
    hypothesis = factory.LazyAttribute(lambda o: faker.text(1000))
    feature_config = factory.SubFactory(
        "experimenter.experiments.tests.factories.NimbusFeatureConfigFactory"
    )

    class Meta:
        model = NimbusExperiment

    @factory.post_generation
    def probe_sets(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if not extracted:
            for i in range(3):
                self.probe_sets.add(NimbusProbeSetFactory.create())

        if extracted:
            # A list of groups were passed in, use them
            for probe_set in extracted:
                self.probe_sets.add(probe_set)

    @classmethod
    def create_with_status(cls, target_status, **kwargs):
        experiment = cls.create(**kwargs)

        NimbusBranchFactory.create(experiment=experiment)
        experiment.control_branch = NimbusBranchFactory.create(experiment=experiment)
        experiment.status = target_status
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


class NimbusFeatureConfigFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusConstants.MAX_SLUG_LEN]
    )
    description = factory.LazyAttribute(lambda o: faker.text(200))
    application = factory.LazyAttribute(
        lambda o: random.choice(NimbusExperiment.Application.choices)[0]
    )
    owner_email = factory.LazyAttribute(lambda o: faker.email())

    class Meta:
        model = NimbusFeatureConfig


class NimbusProbeFactory(factory.django.DjangoModelFactory):
    kind = factory.LazyAttribute(
        lambda o: random.choices(NimbusConstants.ProbeKind.choices)
    )
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    event_category = factory.LazyAttribute(lambda o: slugify(faker.catch_phrase()))
    event_method = factory.LazyAttribute(lambda o: slugify(faker.catch_phrase()))
    event_object = factory.LazyAttribute(lambda o: slugify(faker.catch_phrase()))
    event_value = factory.LazyAttribute(lambda o: slugify(faker.catch_phrase()))

    class Meta:
        model = NimbusProbe


class NimbusProbeSetFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusConstants.MAX_SLUG_LEN]
    )

    class Meta:
        model = NimbusProbeSet

    @factory.post_generation
    def probes(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if not extracted:
            for i in range(3):
                self.probes.add(NimbusProbeFactory.create())

        if extracted:
            # A list of groups were passed in, use them
            for probe in extracted:
                self.probes.add(probe)
