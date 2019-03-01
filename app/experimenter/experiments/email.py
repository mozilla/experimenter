import datetime
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from experimenter.experiments.models import Experiment


def send_review_email(experiment_name, experiment_url, needs_attention):
    attention = Experiment.ATTENTION_MESSAGE if needs_attention else ""

    content = Experiment.REVIEW_EMAIL_TEMPLATE.format(
        experiment_url=urljoin(
            "https://{}".format(settings.HOSTNAME), experiment_url
        ),
        attention=attention,
    )
    send_mail(
        Experiment.REVIEW_EMAIL_SUBJECT.format(name=experiment_name),
        content,
        settings.EMAIL_SENDER,
        [settings.EMAIL_REVIEW],
        fail_silently=False,
    )


def send_intent_to_ship_email(experiment_id, experiment_url):

    def make_url(uri):
        return urljoin("https://{}".format(settings.HOSTNAME), uri)

    # XXX Is there already a routine for doing this?
    def format_date(date, format="%Y-%m-%d"):
        assert isinstance(date, datetime.date)
        return date.strftime(format)

    experiment = Experiment.objects.get(id=experiment_id)

    version = experiment.firefox_version
    channel = experiment.firefox_channel
    experiment_url = make_url(experiment.experiment_url)

    bug_url = settings.BUGZILLA_DETAIL_URL.format(id=experiment.bugzilla_id)

    project_url = make_url(
        reverse("projects-detail", kwargs={"slug": experiment.project.slug})
    )

    proposed_start_date = experiment.proposed_start_date
    proposed_end_date = proposed_start_date + datetime.timedelta(
        days=experiment.proposed_duration
    )
    # Because that's how it's done in Experiment.population (property)
    percent_of_population = f"{experiment.population_percent:g}%"
    # XXX https://github.com/mozilla/experimenter/issues/747#issuecomment-468404348
    platforms = "(unknown)"
    # XXX https://github.com/mozilla/experimenter/issues/747#issuecomment-468407307
    locales = "(unknown)"

    content = Experiment.INTENT_TO_SHIP_EMAIL_TEMPLATE.format(
        experiment_url=experiment_url,
        bug_url=bug_url,
        project_url=project_url,
        experiment_owner=experiment.owner.email,
        short_description=experiment.short_description,
        version=version,
        channel=channel,
        proposed_start_date=format_date(proposed_start_date),
        proposed_end_date=format_date(proposed_end_date),
        percent_of_population=percent_of_population,
        platforms=platforms,
        locales=locales,
        qa_status=experiment.qa_status,
        feature_bugzilla_url=experiment.feature_bugzilla_url,
        related_work=experiment.related_work,
    ).lstrip()
    send_mail(
        Experiment.INTENT_TO_SHIP_EMAIL_SUBJECT.format(
            name=experiment.name, version=version, channel=channel
        ),
        content,
        settings.EMAIL_SENDER,
        [settings.EMAIL_REVIEW],
        fail_silently=False,
    )
