import datetime
import decimal
import json
import random
from collections.abc import Iterable
from enum import Enum

import factory
from django.utils import timezone
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.base.models import Country, Locale
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
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


class LifecycleStates(Enum):
    DRAFT_IDLE = {
        "status": NimbusExperiment.Status.DRAFT,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
    }
    PREVIEW_IDLE = {
        "status": NimbusExperiment.Status.PREVIEW,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
    }
    DRAFT_REVIEW = {
        "status": NimbusExperiment.Status.DRAFT,
        "status_next": NimbusExperiment.Status.LIVE,
        "publish_status": NimbusExperiment.PublishStatus.REVIEW,
    }
    DRAFT_APPROVED = {
        "status": NimbusExperiment.Status.DRAFT,
        "status_next": NimbusExperiment.Status.LIVE,
        "publish_status": NimbusExperiment.PublishStatus.APPROVED,
    }
    DRAFT_WAITING = {
        "status": NimbusExperiment.Status.DRAFT,
        "status_next": NimbusExperiment.Status.LIVE,
        "publish_status": NimbusExperiment.PublishStatus.WAITING,
    }
    LIVE_IDLE = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
    }
    LIVE_IDLE_ENROLLING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
        "is_paused": False,
    }
    LIVE_REVIEW_PAUSING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": NimbusExperiment.Status.LIVE,
        "publish_status": NimbusExperiment.PublishStatus.REVIEW,
        "is_paused": True,
    }
    LIVE_IDLE_REJECT_PAUSING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
        "is_paused": False,
    }
    LIVE_APPROVED_PAUSING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": NimbusExperiment.Status.LIVE,
        "publish_status": NimbusExperiment.PublishStatus.APPROVED,
        "is_paused": True,
    }
    LIVE_WAITING_PAUSING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": NimbusExperiment.Status.LIVE,
        "publish_status": NimbusExperiment.PublishStatus.WAITING,
        "is_paused": True,
    }
    LIVE_IDLE_PAUSED = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
        "is_paused": True,
    }
    LIVE_REVIEW_ENDING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": NimbusExperiment.Status.COMPLETE,
        "publish_status": NimbusExperiment.PublishStatus.REVIEW,
    }
    LIVE_IDLE_REJECT_ENDING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
    }
    LIVE_APPROVED_ENDING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": NimbusExperiment.Status.COMPLETE,
        "publish_status": NimbusExperiment.PublishStatus.APPROVED,
    }
    LIVE_WAITING_ENDING = {
        "status": NimbusExperiment.Status.LIVE,
        "status_next": NimbusExperiment.Status.COMPLETE,
        "publish_status": NimbusExperiment.PublishStatus.WAITING,
    }
    COMPLETE_IDLE = {
        "status": NimbusExperiment.Status.COMPLETE,
        "status_next": None,
        "publish_status": NimbusExperiment.PublishStatus.IDLE,
    }


class Lifecycles(Enum):
    CREATED = (LifecycleStates.DRAFT_IDLE,)
    PREVIEW = CREATED + (LifecycleStates.PREVIEW_IDLE,)
    LAUNCH_REVIEW_REQUESTED = CREATED + (LifecycleStates.DRAFT_REVIEW,)
    LAUNCH_REJECT = LAUNCH_REVIEW_REQUESTED + (LifecycleStates.DRAFT_IDLE,)
    LAUNCH_APPROVE = LAUNCH_REVIEW_REQUESTED + (LifecycleStates.DRAFT_APPROVED,)
    LAUNCH_APPROVE_WAITING = LAUNCH_APPROVE + (LifecycleStates.DRAFT_WAITING,)
    LAUNCH_APPROVE_APPROVE = LAUNCH_APPROVE_WAITING + (LifecycleStates.LIVE_IDLE,)
    LAUNCH_APPROVE_TIMEOUT = LAUNCH_APPROVE_WAITING + (LifecycleStates.DRAFT_REVIEW,)
    LIVE_ENROLLING = LAUNCH_APPROVE_APPROVE + (LifecycleStates.LIVE_IDLE_ENROLLING,)
    PAUSING_REVIEW_REQUESTED = LIVE_ENROLLING + (LifecycleStates.LIVE_REVIEW_PAUSING,)
    PAUSING_REJECT = PAUSING_REVIEW_REQUESTED + (
        LifecycleStates.LIVE_IDLE_REJECT_PAUSING,
    )
    PAUSING_APPROVE = PAUSING_REVIEW_REQUESTED + (LifecycleStates.LIVE_APPROVED_PAUSING,)
    PAUSING_APPROVE_WAITING = PAUSING_APPROVE + (LifecycleStates.LIVE_WAITING_PAUSING,)
    PAUSING_APPROVE_APPROVE = PAUSING_APPROVE_WAITING + (LifecycleStates.LIVE_IDLE,)
    PAUSING_APPROVE_REJECT = PAUSING_APPROVE_WAITING + (
        LifecycleStates.LIVE_IDLE_REJECT_PAUSING,
    )
    PAUSING_APPROVE_TIMEOUT = PAUSING_APPROVE_WAITING + (
        LifecycleStates.LIVE_REVIEW_PAUSING,
    )
    LIVE_PAUSED = LIVE_ENROLLING + (LifecycleStates.LIVE_IDLE_PAUSED,)
    ENDING_REVIEW_REQUESTED = LIVE_PAUSED + (LifecycleStates.LIVE_REVIEW_ENDING,)
    ENDING_APPROVE = ENDING_REVIEW_REQUESTED + (LifecycleStates.LIVE_APPROVED_ENDING,)
    ENDING_APPROVE_WAITING = ENDING_APPROVE + (LifecycleStates.LIVE_WAITING_ENDING,)
    ENDING_APPROVE_APPROVE = ENDING_APPROVE_WAITING + (LifecycleStates.COMPLETE_IDLE,)
    ENDING_APPROVE_REJECT = ENDING_APPROVE_WAITING + (
        LifecycleStates.LIVE_IDLE_REJECT_ENDING,
    )
    ENDING_APPROVE_TIMEOUT = ENDING_APPROVE_WAITING + (
        LifecycleStates.LIVE_REVIEW_ENDING,
    )


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
        exclude = ("Lifecycles", "LifecycleStates")

    Lifecycles = Lifecycles
    LifecycleStates = LifecycleStates

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
    def create_with_lifecycle(cls, lifecycle, with_random_timespan=False, **kwargs):
        experiment = cls.create(**kwargs)
        now = timezone.now() - datetime.timedelta(days=random.randint(100, 200))

        for state in lifecycle.value:
            experiment.apply_lifecycle_state(state)

            if (
                experiment.status == experiment.Status.LIVE
                and experiment.status_next is None
            ):
                experiment.published_dto = NimbusExperimentSerializer(experiment).data

            experiment.save()

            if experiment.has_filter(experiment.Filters.SHOULD_ALLOCATE_BUCKETS):
                experiment.allocate_bucket_range()

            change = generate_nimbus_changelog(
                experiment,
                experiment.owner,
                f"set lifecycle {lifecycle} state {state}",
            )

            if with_random_timespan:
                change.changed_on = now
                change.save()
                now += datetime.timedelta(days=random.randint(5, 20))

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
