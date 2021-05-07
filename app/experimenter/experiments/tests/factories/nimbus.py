import decimal
import json
import random
from collections.abc import Iterable

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.base.models import Country, Locale
from experimenter.experiments.changelog_utils import (
    NimbusExperimentChangeLogSerializer,
    generate_nimbus_changelog,
)
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
)
from experimenter.experiments.models.nimbus import NimbusChangeLog
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.projects.tests.factories import ProjectFactory

faker = FakerFactory.create()


class NimbusExperimentFactory(factory.django.DjangoModelFactory):
    publish_status = NimbusExperiment.PublishStatus.IDLE
    owner = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusExperiment.MAX_SLUG_LEN]
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
    risk_partner_related = factory.LazyAttribute(lambda o: random.choice([True, False]))
    risk_revenue = factory.LazyAttribute(lambda o: random.choice([True, False]))
    risk_brand = factory.LazyAttribute(lambda o: random.choice([True, False]))

    class Meta:
        model = NimbusExperiment

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

    @factory.post_generation
    def locales(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted is None and Locale.objects.exists():
            extracted = Locale.objects.all()[:3]

        if extracted:
            self.locales.add(*extracted)

    @factory.post_generation
    def countries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted is None and Country.objects.exists():
            extracted = Country.objects.all()[:3]

        if extracted:
            self.countries.add(*extracted)

    @classmethod
    def create_with_lifecycle(cls, lifecycle, **kwargs):
        experiment = cls.create(**kwargs)

        for state in lifecycle.value:
            experiment.apply_lifecycle_state(state)
            experiment.save()

            if experiment.has_filter(experiment.Filters.SHOULD_ALLOCATE_BUCKETS):
                experiment.allocate_bucket_range()

            generate_nimbus_changelog(
                experiment,
                experiment.owner,
                f"set lifecycle {lifecycle} state {state}",
            )

        return NimbusExperiment.objects.get(id=experiment.id)


class NimbusBranchFactory(factory.django.DjangoModelFactory):
    ratio = 1
    experiment = factory.SubFactory(NimbusExperimentFactory)
    name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    slug = factory.LazyAttribute(
        lambda o: slugify(o.name)[: NimbusExperiment.MAX_SLUG_LEN]
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
        lambda o: slugify(o.name)[: NimbusExperiment.MAX_SLUG_LEN]
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
