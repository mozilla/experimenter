import datetime
import json
from collections import defaultdict

from django.utils.text import slugify

from experimenter.projects.models import Project
from experimenter.experiments.models import Experiment, ExperimentVariant

experiments_data = json.loads(open('experiments.json', 'rb').read())

activity_stream, created = Project.objects.get_or_create(name='Activity Stream', slug='activity-stream')

version_data = [row.split(',') for row in open('versions.csv', 'r').read().splitlines()]
versions = defaultdict(list)
for experiment_id, version in version_data:
    versions[experiment_id].append(version)

dates_data = [row.split(',') for row in open('experiment_dates.csv', 'r').read().splitlines()]
all_dates = defaultdict(list)
for experiment_id, date in dates_data:
    all_dates[experiment_id].append(date)

experiment_dates = defaultdict(dict)
for experiment_id in all_dates.keys():
    experiment_dates[experiment_id]['start_date'] = all_dates[experiment_id][0]
    experiment_dates[experiment_id]['end_date'] = all_dates[experiment_id][-1]

print(experiment_dates)

for data in experiments_data.values():
    experiment = Experiment(
        project=activity_stream,
        name=data['name'],
        slug=data['variant']['id'],
        objectives=data['description'],
        success_criteria='TODO',
        analysis='TODO',
        addon_versions=versions.get(data['variant']['id'], ['1.0']),
    )

    experiment.save()

    experiment.status = Experiment.EXPERIMENT_STARTED
    experiment.save()

    experiment.status = Experiment.EXPERIMENT_COMPLETE
    experiment.save()

    if experiment.slug in experiment_dates:
        experiment.start_date = datetime.datetime.strptime(experiment_dates[experiment.slug]['start_date'], '%Y-%m-%d')
        experiment.end_date = datetime.datetime.strptime(experiment_dates[experiment.slug]['end_date'], '%Y-%m-%d')
        experiment.save()

    control_variant = ExperimentVariant(
        experiment=experiment,
        is_control=True,
        name='Control',
        slug='control',
        description=data['control']['description'],
        value=data['control']['value'],
    )
    control_variant.save()

    experiment_variant = ExperimentVariant(
        experiment=experiment,
        is_control=False,
        name='Variant',
        slug='variant',
        description=data['variant']['description'],
        threshold=data['variant']['threshold'],
        value=data['variant']['value'],
    )
    experiment_variant.save()
