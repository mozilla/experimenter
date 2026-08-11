import pytest


@pytest.mark.nimbus_ui
def test_rollout_can_be_launched(configured_rollout, kinto_client):
    configured_rollout.transition_to_preview()
    assert configured_rollout.is_in_preview

    configured_rollout.request_enrollment()
    configured_rollout.approve_review()
    kinto_client().approve()
    configured_rollout.wait_for_live_status()
    configured_rollout.wait_for_rollout_phase(1)


@pytest.mark.nimbus_ui
def test_rollout_can_be_disabled_and_reenabled(live_rollout, kinto_client):
    live_rollout.request_disable()
    live_rollout.approve_review()
    kinto_client().approve()
    live_rollout.wait_for_disabled_status()

    live_rollout.request_reenable()
    live_rollout.approve_review()
    kinto_client().approve()
    live_rollout.wait_for_live_status()
    live_rollout.wait_for_rollout_phase(2)


@pytest.mark.nimbus_ui
def test_rollout_can_advance_phase(live_rollout, kinto_client):
    live_rollout.request_phase_advance()
    live_rollout.approve_review()
    kinto_client().approve()
    live_rollout.wait_for_rollout_phase(2)


@pytest.mark.nimbus_ui
def test_rollout_can_be_cloned(selenium, create_rollout, default_data):
    rollout = create_rollout(selenium)
    original_url = selenium.current_url
    clone_name = f"{default_data.public_name} Clone"

    rollout.open_clone_modal()
    rollout.clone_name = clone_name
    rollout.submit_clone()

    assert selenium.current_url != original_url
    assert rollout.header_name == clone_name


@pytest.mark.nimbus_ui
def test_rollout_can_be_archived(selenium, create_rollout):
    rollout = create_rollout(selenium)

    assert not rollout.is_archived

    rollout.toggle_archive()

    assert rollout.is_archived
