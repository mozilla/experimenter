import decimal
import json
import random
from collections.abc import Iterable

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.experiments.changelog_utils import (
    NimbusExperimentChangeLogSerializer,
    generate_nimbus_changelog,
)
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
    NimbusProbe,
    NimbusProbeSet,
)
from experimenter.experiments.models.nimbus import NimbusChangeLog
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.projects.tests.factories import ProjectFactory

faker = FakerFactory.create()


class NimbusExperimentFactory(factory.django.DjangoModelFactory):
    owner = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusConstants.MAX_SLUG_LEN]
    )
    public_description = factory.LazyAttribute(lambda o: faker.text(200))
    risk_mitigation_link = factory.LazyAttribute(lambda o: faker.uri())
    proposed_duration = factory.LazyAttribute(lambda o: random.randint(10, 60))
    proposed_enrollment = factory.LazyAttribute(
        lambda o: random.randint(2, o.proposed_duration)
    )
    population_percent = factory.LazyAttribute(
        lambda o: decimal.Decimal(random.randint(1, 10) * 10)
    )
    total_enrolled_clients = factory.LazyAttribute(
        lambda o: random.randint(1, 100) * 1000
    )
    firefox_min_version = factory.LazyAttribute(
        lambda o: random.choice(list(NimbusExperiment.Version)).value
    )
    application = factory.LazyAttribute(
        lambda o: random.choice(list(NimbusExperiment.Application)).value
    )
    channel = factory.LazyAttribute(
        lambda o: random.choice(list(NimbusExperiment.Channel)).value
    )
    hypothesis = factory.LazyAttribute(lambda o: faker.text(1000))
    feature_config = factory.SubFactory(
        "experimenter.experiments.tests.factories.NimbusFeatureConfigFactory"
    )
    targeting_config_slug = factory.LazyAttribute(
        lambda o: random.choice(list(NimbusExperiment.TargetingConfig)).value
    )
    primary_outcomes = factory.LazyAttribute(
        lambda o: [oc.slug for oc in Outcomes.all()[:2]]
    )
    secondary_outcomes = factory.LazyAttribute(
        lambda o: [oc.slug for oc in Outcomes.all()[2:]]
    )

    class Meta:
        model = NimbusExperiment

    @factory.post_generation
    def probe_sets(self, create, extracted, **kwargs):
        is_primary = kwargs.pop("is_primary", True)
        if not create:
            # Simple build, do nothing.
            return

        if isinstance(extracted, Iterable):
            # A list of groups were passed in, use them
            for probe_set in extracted:
                self.probe_sets.add(
                    probe_set, through_defaults={"is_primary": is_primary}
                )
        else:
            for i in range(3):
                self.probe_sets.add(
                    NimbusProbeSetFactory.create(),
                    through_defaults={"is_primary": is_primary},
                )

    @factory.post_generation
    def projects(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if isinstance(extracted, Iterable):
            # A list of groups were passed in, use them
            for project in extracted:
                self.projects.add(project)
        else:
            for i in range(3):
                self.projects.add(ProjectFactory.create())

    @factory.post_generation
    def branches(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if isinstance(extracted, Iterable):
            # A list of groups were passed in, use them
            for branch in extracted:
                self.branches.add(branch)
        else:
            NimbusBranchFactory.create(experiment=self)
            self.reference_branch = NimbusBranchFactory.create(experiment=self)
            self.save()

    @factory.post_generation
    def document_links(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if isinstance(extracted, Iterable):
            # A list of links were passed in, use them
            for link in extracted:
                self.documentation_links.add(link)
        else:
            for title, _ in NimbusExperiment.DocumentationLink.choices:
                self.documentation_links.add(
                    NimbusDocumentationLinkFactory.create_with_title(
                        experiment=self, title=title
                    )
                )

    @classmethod
    def create_with_status(cls, target_status, **kwargs):
        experiment = cls.create(**kwargs)

        for status, _ in NimbusExperiment.Status.choices:
            if status == NimbusExperiment.Status.PREVIEW and status != target_status:
                # HACK: exclude PREVIEW status from the usual mock sequence
                continue

            experiment.status = status
            experiment.save()

            if experiment.should_allocate_bucket_range:
                experiment.allocate_bucket_range()

            generate_nimbus_changelog(experiment, experiment.owner)

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
    feature_value = factory.LazyAttribute(
        lambda o: json.dumps({faker.slug(): faker.slug()})
    )

    class Meta:
        model = NimbusBranch


class NimbusDocumentationLinkFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(NimbusExperimentFactory)
    title = factory.LazyAttribute(lambda o: faker.catch_phrase())
    link = factory.LazyAttribute(lambda o: faker.uri())

    class Meta:
        model = NimbusDocumentationLink

    @classmethod
    def create_with_title(cls, title, experiment):
        return cls.create(
            title=title,
            experiment=experiment,
        )


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


FAKER_JSON_SCHEMA = """\
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "Fake schema that matches NimbusBranchFactory feature_value factory",
    "type": "object",
    "patternProperties": {
        "^.*$": { "type": "string" }
    },
    "additionalProperties": false
}
"""


class NimbusFeatureConfigFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusConstants.MAX_SLUG_LEN]
    )
    description = factory.LazyAttribute(lambda o: faker.text(200))
    application = factory.LazyAttribute(
        lambda o: random.choice(list(NimbusExperiment.Application)).value
    )
    owner_email = factory.LazyAttribute(lambda o: faker.email())
    schema = factory.LazyAttribute(
        lambda o: faker.random_element(
            elements=(
                None,
                FAKER_JSON_SCHEMA,
            )
        )
    )

    class Meta:
        model = NimbusFeatureConfig


class NimbusProbeFactory(factory.django.DjangoModelFactory):
    kind = factory.LazyAttribute(
        lambda o: random.choice(list(NimbusConstants.ProbeKind)).value
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


class NimbusChangeLogFactory(factory.django.DjangoModelFactory):
    experiment = factory.SubFactory(NimbusExperimentFactory)
    changed_by = factory.SubFactory(UserFactory)
    old_status = NimbusExperiment.Status.DRAFT
    new_status = NimbusExperiment.Status.DRAFT
    message = factory.LazyAttribute(lambda o: faker.catch_phrase())
    experiment_data = factory.LazyAttribute(
        lambda o: dict(NimbusExperimentChangeLogSerializer(o.experiment).data)
    )

    class Meta:
        model = NimbusChangeLog
