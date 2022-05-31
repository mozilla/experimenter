import pytest
from nimbus.pages.experimenter.summary import SummaryPage


@pytest.mark.run_per_app
def test_create_new_experiment_approve_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()


@pytest.mark.run_once
def test_create_new_experiment_reject_remote_settings(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()


@pytest.mark.run_once
def test_create_new_experiment_timeout_remote_settings(
    selenium,
    create_experiment,
):
    summary = create_experiment(selenium)
    summary.launch_and_approve()
    summary.wait_for_timeout_alert()


@pytest.mark.run_once
def test_end_experiment_and_approve_end(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_complete_status()


@pytest.mark.run_once
def test_end_experiment_and_reject_end(
    selenium,
    experiment_url,
    create_experiment,
    kinto_client,
):
    create_experiment(selenium).launch_and_approve()

    kinto_client.approve()

    summary = SummaryPage(selenium, experiment_url).open()
    summary.wait_for_live_status()
    summary.end_and_approve()

    kinto_client.reject()

    SummaryPage(selenium, experiment_url).open().wait_for_rejected_alert()
