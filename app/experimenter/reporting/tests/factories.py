import random
from datetime import datetime

import factory
from django.utils.text import slugify
from faker import Factory as FakerFactory

from experimenter.projects.tests.factories import ProjectFactory
from experimenter.reporting.constants import ReportLogConstants
from experimenter.reporting.models import ReportLog

faker = FakerFactory.create()


class ReportLogFactory(ReportLogConstants, factory.django.DjangoModelFactory):
    timestamp = datetime.now()
    experiment_name = factory.LazyAttribute(lambda o: faker.catch_phrase())
    experiment_slug = factory.LazyAttribute(
        lambda o: "{}_".format(slugify(o.experiment_name))
    )
    comment = factory.LazyAttribute(lambda o: faker.text(200))
    experiment_old_status = factory.LazyAttribute(
        lambda o: random.choice(ReportLogConstants.ExperimentStatus.choices[1:])[0]
    )
    experiment_new_status = factory.LazyAttribute(
        lambda o: random.choice(ReportLogConstants.ExperimentStatus.choices[1:])[0]
    )
    event = factory.LazyAttribute(
        lambda o: random.choice(ReportLogConstants.Event.choices[1:])[0]
    )
    event_reason = factory.LazyAttribute(
        lambda o: random.choice(ReportLogConstants.EVENT_PAIRS[o.event])
    )

    class Meta:
        model = ReportLog

    @factory.post_generation
    def projects(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted is None:

            extracted = [ProjectFactory.create() for i in range(3)]

        self.projects.add(*extracted)
